# Copyright (c) 2025 Contributors to the microchip-emc2305 project
# SPDX-License-Identifier: MIT

"""
Mock I2C Bus for Unit Testing

Provides a mock I2C bus implementation for testing EMC2305 driver logic
without requiring actual hardware.
"""

import threading
from typing import Dict, Optional
from emc2305.driver.i2c import I2CError


class MockI2CBus:
    """
    Mock I2C bus for unit testing.

    Simulates an EMC2305 device with register storage and basic behavior.
    """

    def __init__(self, device_address: int = 0x4D):
        """
        Initialize mock I2C bus.

        Args:
            device_address: I2C address of simulated EMC2305 device
        """
        self.device_address = device_address
        self._registers: Dict[int, int] = {}
        self._lock = threading.Lock()
        self._initialize_default_registers()

    def _initialize_default_registers(self) -> None:
        """Initialize registers with EMC2305 default values."""
        # Product identification
        self._registers[0xFD] = 0x34  # Product ID
        self._registers[0xFE] = 0x5D  # Manufacturer ID (SMSC)
        self._registers[0xFF] = 0x80  # Revision

        # Configuration register (0x20)
        self._registers[0x20] = 0x00  # Default: all disabled

        # PWM polarity (0x2A) - default normal
        self._registers[0x2A] = 0x00

        # PWM output config (0x2B) - default push-pull
        self._registers[0x2B] = 0x00

        # PWM base frequencies (0x2C, 0x2D) - default 26kHz
        self._registers[0x2C] = 0x00
        self._registers[0x2D] = 0x00

        # Initialize fan channel registers (5 channels)
        for channel in range(5):
            base = 0x30 + (channel * 0x10)

            # Fan Setting register - default 0xFF (100%)
            self._registers[base + 0x00] = 0xFF

            # PWM Divide - default 1
            self._registers[base + 0x01] = 0x01

            # CONFIG1 - default 200ms update, 5 edges (2-pole)
            self._registers[base + 0x02] = 0x28

            # CONFIG2 - default no error range, no derivative
            self._registers[base + 0x03] = 0x00

            # Gain register - default P=2x, I=1x, D=1x
            self._registers[base + 0x05] = 0x48

            # Spin-up config - default 50%, 500ms
            self._registers[base + 0x06] = 0x8A

            # Max step - default 255 (no limiting)
            self._registers[base + 0x07] = 0xFF

            # Minimum drive - default 0
            self._registers[base + 0x08] = 0x00

            # Valid TACH count - default 0x0FFF
            self._registers[base + 0x09] = 0x0F

            # Drive fail band low/high
            self._registers[base + 0x0A] = 0x00
            self._registers[base + 0x0B] = 0x00

            # TACH target low/high - default 0xFFFF (max)
            self._registers[base + 0x0C] = 0xFF
            self._registers[base + 0x0D] = 0xFF

            # TACH reading high/low - simulate 3000 RPM
            # For 2-pole fan (5 edges): count = (32000 * 60) / (3000 * 5) = 128
            self._registers[base + 0x0E] = 0x00  # High byte
            self._registers[base + 0x0F] = 0x80  # Low byte (128)

        # Status registers - default no faults
        self._registers[0x24] = 0x00  # Fan status
        self._registers[0x25] = 0x00  # Stall status
        self._registers[0x26] = 0x00  # Spin status
        self._registers[0x27] = 0x00  # Drive fail status

        # Fan interrupt enable - default disabled
        self._registers[0x29] = 0x00

        # Software lock - default unlocked
        self._registers[0xEF] = 0x00

        # Product features register
        self._registers[0xFC] = 0x0D  # 5 fans (bits 0-2=5), RPM control (bit 3=1)

    def read_byte(self, device_address: int, register: int) -> int:
        """
        Read byte from register.

        Args:
            device_address: I2C device address
            register: Register address to read from

        Returns:
            Register value (0-255)

        Raises:
            I2CError: If device address doesn't match or register doesn't exist
        """
        if device_address != self.device_address:
            raise I2CError(
                f"Device not found at address 0x{device_address:02X}. "
                f"Mock device is at 0x{self.device_address:02X}"
            )

        with self._lock:
            if register not in self._registers:
                # Return 0 for uninitialized registers (realistic behavior)
                return 0x00
            return self._registers[register]

    def write_byte(self, device_address: int, register: int, value: int) -> None:
        """
        Write byte to register.

        Args:
            device_address: I2C device address
            register: Register address to write to
            value: Value to write (0-255)

        Raises:
            I2CError: If device address doesn't match
            ValueError: If value is out of range
        """
        if device_address != self.device_address:
            raise I2CError(
                f"Device not found at address 0x{device_address:02X}. "
                f"Mock device is at 0x{self.device_address:02X}"
            )

        if not 0 <= value <= 255:
            raise ValueError(f"Value must be 0-255, got {value}")

        if not 0 <= register <= 255:
            raise ValueError(f"Register must be 0-255, got {register}")

        with self._lock:
            self._registers[register] = value

    def read_block(self, device_address: int, register: int, length: int) -> bytes:
        """
        Read block of bytes starting from register.

        Args:
            device_address: I2C device address
            register: Starting register address
            length: Number of bytes to read

        Returns:
            Bytes object containing register values

        Raises:
            I2CError: If device address doesn't match
        """
        if device_address != self.device_address:
            raise I2CError(
                f"Device not found at address 0x{device_address:02X}. "
                f"Mock device is at 0x{self.device_address:02X}"
            )

        with self._lock:
            data = []
            for i in range(length):
                reg = register + i
                if reg in self._registers:
                    data.append(self._registers[reg])
                else:
                    data.append(0x00)
            return bytes(data)

    def write_block(self, device_address: int, register: int, data: bytes) -> None:
        """
        Write block of bytes starting from register.

        Args:
            device_address: I2C device address
            register: Starting register address
            data: Bytes to write

        Raises:
            I2CError: If device address doesn't match
        """
        if device_address != self.device_address:
            raise I2CError(
                f"Device not found at address 0x{device_address:02X}. "
                f"Mock device is at 0x{self.device_address:02X}"
            )

        with self._lock:
            for i, byte_val in enumerate(data):
                self._registers[register + i] = byte_val

    def get_register(self, register: int) -> Optional[int]:
        """
        Get register value (for test verification).

        Args:
            register: Register address

        Returns:
            Register value or None if not set
        """
        with self._lock:
            return self._registers.get(register)

    def set_register(self, register: int, value: int) -> None:
        """
        Set register value (for test setup).

        Args:
            register: Register address
            value: Value to set (0-255)
        """
        with self._lock:
            self._registers[register] = value

    def reset(self) -> None:
        """Reset all registers to default values."""
        with self._lock:
            self._registers.clear()
            self._initialize_default_registers()

    def simulate_fault(self, fault_type: str, channel: int = 1) -> None:
        """
        Simulate a hardware fault for testing.

        Args:
            fault_type: Type of fault ('stall', 'spin', 'drive_fail')
            channel: Fan channel (1-5)
        """
        if not 1 <= channel <= 5:
            raise ValueError(f"Channel must be 1-5, got {channel}")

        bit_mask = 1 << (channel - 1)

        with self._lock:
            if fault_type == "stall":
                self._registers[0x24] |= bit_mask  # Fan status
                self._registers[0x25] |= bit_mask  # Stall status
            elif fault_type == "spin":
                self._registers[0x24] |= bit_mask  # Fan status
                self._registers[0x26] |= bit_mask  # Spin status
            elif fault_type == "drive_fail":
                self._registers[0x24] |= bit_mask  # Fan status
                self._registers[0x27] |= bit_mask  # Drive fail status
            else:
                raise ValueError(
                    f"Unknown fault type: {fault_type}. "
                    f"Must be 'stall', 'spin', or 'drive_fail'"
                )

    def clear_faults(self) -> None:
        """Clear all fault status registers."""
        with self._lock:
            self._registers[0x24] = 0x00  # Fan status
            self._registers[0x25] = 0x00  # Stall status
            self._registers[0x26] = 0x00  # Spin status
            self._registers[0x27] = 0x00  # Drive fail status
