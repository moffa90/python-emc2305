# Copyright (c) 2025 Contributors to the microchip-emc2305 project
# SPDX-License-Identifier: MIT

"""
I2C Communication Layer

Provides low-level I2C communication with cross-process locking support.
"""

import logging
import time
from pathlib import Path
from typing import Any, Optional

try:
    import smbus2
except ImportError:
    smbus2 = None

from filelock import FileLock, Timeout

from emc2305.driver.constants import (
    DEFAULT_I2C_BUS,
    DEFAULT_I2C_LOCK_PATH,
    DEFAULT_I2C_LOCK_TIMEOUT,
    MAX_I2C_ADDRESS,
    MAX_REGISTER_ADDRESS,
    MIN_I2C_ADDRESS,
    MIN_REGISTER_ADDRESS,
    READ_DELAY_MS,
    SMBUS_BLOCK_MAX_LENGTH,
    WRITE_DELAY_MS,
)

logger = logging.getLogger(__name__)


class I2CError(Exception):
    """Base exception for I2C communication errors."""

    pass


class I2CBusLockError(I2CError):
    """Raised when I2C bus lock cannot be acquired."""

    pass


class I2CBus:
    """
    I2C bus communication with cross-process locking.

    Provides thread-safe and process-safe I2C operations using file-based locks.

    Args:
        bus_number: I2C bus number (default: 0)
        lock_enabled: Enable cross-process locking (default: True)
        lock_timeout: Lock acquisition timeout in seconds (default: 5.0)
        lock_path: Directory for lock files (default: /var/lock)

    Example:
        >>> bus = I2CBus(bus_number=0)
        >>> value = bus.read_byte(0x2F, 0x00)
        >>> bus.write_byte(0x2F, 0x01, 0xFF)
    """

    def __init__(
        self,
        bus_number: int = DEFAULT_I2C_BUS,
        lock_enabled: bool = True,
        lock_timeout: float = DEFAULT_I2C_LOCK_TIMEOUT,
        lock_path: str = DEFAULT_I2C_LOCK_PATH,
    ):
        if smbus2 is None:
            raise ImportError(
                "smbus2 is required for I2C communication. " "Install with: pip install smbus2"
            )

        self.bus_number = bus_number
        self.lock_enabled = lock_enabled
        self.lock_timeout = lock_timeout

        # Initialize I2C bus
        try:
            self.bus = smbus2.SMBus(bus_number)
        except Exception as e:
            raise I2CError(f"Failed to open I2C bus {bus_number}: {e}")

        # Initialize lock if enabled
        self.lock: Optional[FileLock] = None
        if self.lock_enabled:
            lock_file = Path(lock_path) / f"i2c-{bus_number}.lock"
            lock_file.parent.mkdir(parents=True, exist_ok=True)
            self.lock = FileLock(str(lock_file), timeout=lock_timeout)
            logger.debug(f"I2C bus {bus_number} locking enabled: {lock_file}")

    def _validate_address(self, address: int) -> None:
        """
        Validate I2C device address.

        Args:
            address: I2C device address (7-bit)

        Raises:
            I2CError: If address is out of valid range
        """
        if not MIN_I2C_ADDRESS <= address <= MAX_I2C_ADDRESS:
            raise I2CError(
                f"Invalid I2C address: 0x{address:02X} "
                f"(must be 0x{MIN_I2C_ADDRESS:02X}-0x{MAX_I2C_ADDRESS:02X})"
            )

    def _validate_register(self, register: int) -> None:
        """
        Validate register address.

        Args:
            register: Register address

        Raises:
            I2CError: If register address is out of valid range
        """
        if not MIN_REGISTER_ADDRESS <= register <= MAX_REGISTER_ADDRESS:
            raise I2CError(
                f"Invalid register address: 0x{register:02X} "
                f"(must be 0x{MIN_REGISTER_ADDRESS:02X}-0x{MAX_REGISTER_ADDRESS:02X})"
            )

    def _validate_block_length(self, length: int) -> None:
        """
        Validate block read/write length.

        Args:
            length: Number of bytes to read/write

        Raises:
            I2CError: If length exceeds SMBus limit
        """
        if not 1 <= length <= SMBUS_BLOCK_MAX_LENGTH:
            raise I2CError(
                f"Invalid block length: {length} "
                f"(must be 1-{SMBUS_BLOCK_MAX_LENGTH} bytes for SMBus)"
            )

    def _validate_byte_value(self, value: int) -> None:
        """
        Validate byte value.

        Args:
            value: Byte value to validate

        Raises:
            I2CError: If value is out of byte range
        """
        if not 0 <= value <= 0xFF:
            raise I2CError(f"Invalid byte value: 0x{value:X} (must be 0x00-0xFF)")

    def read_byte(self, address: int, register: int) -> int:
        """
        Read a single byte from a register.

        Args:
            address: I2C device address (7-bit)
            register: Register address

        Returns:
            Byte value read from register

        Raises:
            I2CError: If read operation fails or parameters are invalid
            I2CBusLockError: If lock cannot be acquired
        """
        self._validate_address(address)
        self._validate_register(register)

        if self.lock_enabled and self.lock:
            try:
                with self.lock:
                    return self._read_byte_unlocked(address, register)
            except Timeout:
                raise I2CBusLockError(f"Failed to acquire I2C bus lock within {self.lock_timeout}s")
        else:
            return self._read_byte_unlocked(address, register)

    def _read_byte_unlocked(self, address: int, register: int) -> int:
        """Internal read operation without locking."""
        try:
            time.sleep(READ_DELAY_MS / 1000.0)
            value = self.bus.read_byte_data(address, register)
            logger.debug(f"I2C read: addr=0x{address:02X} reg=0x{register:02X} -> 0x{value:02X}")
            return value
        except Exception as e:
            raise I2CError(f"I2C read failed: addr=0x{address:02X} reg=0x{register:02X}: {e}")

    def write_byte(self, address: int, register: int, value: int) -> None:
        """
        Write a single byte to a register.

        Args:
            address: I2C device address (7-bit)
            register: Register address
            value: Byte value to write

        Raises:
            I2CError: If write operation fails or parameters are invalid
            I2CBusLockError: If lock cannot be acquired
        """
        self._validate_address(address)
        self._validate_register(register)
        self._validate_byte_value(value)

        if self.lock_enabled and self.lock:
            try:
                with self.lock:
                    self._write_byte_unlocked(address, register, value)
            except Timeout:
                raise I2CBusLockError(f"Failed to acquire I2C bus lock within {self.lock_timeout}s")
        else:
            self._write_byte_unlocked(address, register, value)

    def _write_byte_unlocked(self, address: int, register: int, value: int) -> None:
        """Internal write operation without locking."""
        try:
            time.sleep(WRITE_DELAY_MS / 1000.0)
            self.bus.write_byte_data(address, register, value)
            logger.debug(f"I2C write: addr=0x{address:02X} reg=0x{register:02X} <- 0x{value:02X}")
        except Exception as e:
            raise I2CError(f"I2C write failed: addr=0x{address:02X} reg=0x{register:02X}: {e}")

    def read_word(self, address: int, register: int) -> int:
        """
        Read a 16-bit word from a register.

        Args:
            address: I2C device address (7-bit)
            register: Register address

        Returns:
            16-bit word value read from register
        """
        if self.lock_enabled and self.lock:
            try:
                with self.lock:
                    return self._read_word_unlocked(address, register)
            except Timeout:
                raise I2CBusLockError(f"Failed to acquire I2C bus lock within {self.lock_timeout}s")
        else:
            return self._read_word_unlocked(address, register)

    def _read_word_unlocked(self, address: int, register: int) -> int:
        """Internal word read operation without locking."""
        try:
            time.sleep(READ_DELAY_MS / 1000.0)
            value = self.bus.read_word_data(address, register)
            logger.debug(
                f"I2C read word: addr=0x{address:02X} reg=0x{register:02X} -> 0x{value:04X}"
            )
            return value
        except Exception as e:
            raise I2CError(f"I2C word read failed: addr=0x{address:02X} reg=0x{register:02X}: {e}")

    def write_word(self, address: int, register: int, value: int) -> None:
        """
        Write a 16-bit word to a register.

        Args:
            address: I2C device address (7-bit)
            register: Register address
            value: 16-bit word value to write
        """
        if self.lock_enabled and self.lock:
            try:
                with self.lock:
                    self._write_word_unlocked(address, register, value)
            except Timeout:
                raise I2CBusLockError(f"Failed to acquire I2C bus lock within {self.lock_timeout}s")
        else:
            self._write_word_unlocked(address, register, value)

    def _write_word_unlocked(self, address: int, register: int, value: int) -> None:
        """Internal word write operation without locking."""
        try:
            time.sleep(WRITE_DELAY_MS / 1000.0)
            self.bus.write_word_data(address, register, value)
            logger.debug(
                f"I2C write word: addr=0x{address:02X} reg=0x{register:02X} <- 0x{value:04X}"
            )
        except Exception as e:
            raise I2CError(f"I2C word write failed: addr=0x{address:02X} reg=0x{register:02X}: {e}")

    def read_block(self, address: int, register: int, length: int) -> list[int]:
        """
        Read a block of bytes from consecutive registers.

        Args:
            address: I2C device address (7-bit)
            register: Starting register address
            length: Number of bytes to read

        Returns:
            List of byte values read from registers

        Raises:
            I2CError: If read operation fails or parameters are invalid
            I2CBusLockError: If lock cannot be acquired
        """
        self._validate_address(address)
        self._validate_register(register)
        self._validate_block_length(length)

        if self.lock_enabled and self.lock:
            try:
                with self.lock:
                    return self._read_block_unlocked(address, register, length)
            except Timeout:
                raise I2CBusLockError(f"Failed to acquire I2C bus lock within {self.lock_timeout}s")
        else:
            return self._read_block_unlocked(address, register, length)

    def _read_block_unlocked(self, address: int, register: int, length: int) -> list[int]:
        """Internal block read operation without locking."""
        try:
            time.sleep(READ_DELAY_MS / 1000.0)
            data = self.bus.read_i2c_block_data(address, register, length)
            logger.debug(
                f"I2C read block: addr=0x{address:02X} reg=0x{register:02X} len={length} -> {[hex(b) for b in data]}"
            )
            return data
        except Exception as e:
            raise I2CError(f"I2C block read failed: addr=0x{address:02X} reg=0x{register:02X}: {e}")

    def write_block(self, address: int, register: int, data: list[int]) -> None:
        """
        Write a block of bytes to consecutive registers.

        Args:
            address: I2C device address (7-bit)
            register: Starting register address
            data: List of byte values to write

        Raises:
            I2CError: If write operation fails or parameters are invalid
            I2CBusLockError: If lock cannot be acquired
        """
        self._validate_address(address)
        self._validate_register(register)
        self._validate_block_length(len(data))
        for value in data:
            self._validate_byte_value(value)

        if self.lock_enabled and self.lock:
            try:
                with self.lock:
                    self._write_block_unlocked(address, register, data)
            except Timeout:
                raise I2CBusLockError(f"Failed to acquire I2C bus lock within {self.lock_timeout}s")
        else:
            self._write_block_unlocked(address, register, data)

    def _write_block_unlocked(self, address: int, register: int, data: list[int]) -> None:
        """Internal block write operation without locking."""
        try:
            time.sleep(WRITE_DELAY_MS / 1000.0)
            self.bus.write_i2c_block_data(address, register, data)
            logger.debug(
                f"I2C write block: addr=0x{address:02X} reg=0x{register:02X} <- {[hex(b) for b in data]}"
            )
        except Exception as e:
            raise I2CError(
                f"I2C block write failed: addr=0x{address:02X} reg=0x{register:02X}: {e}"
            )

    def send_byte(self, address: int, value: int) -> None:
        """
        Send a single byte without a register address (SMBus Send Byte).

        Args:
            address: I2C device address (7-bit)
            value: Byte value to send

        Raises:
            I2CError: If send operation fails
            I2CBusLockError: If lock cannot be acquired
        """
        if self.lock_enabled and self.lock:
            try:
                with self.lock:
                    self._send_byte_unlocked(address, value)
            except Timeout:
                raise I2CBusLockError(f"Failed to acquire I2C bus lock within {self.lock_timeout}s")
        else:
            self._send_byte_unlocked(address, value)

    def _send_byte_unlocked(self, address: int, value: int) -> None:
        """Internal send byte operation without locking."""
        try:
            time.sleep(WRITE_DELAY_MS / 1000.0)
            self.bus.write_byte(address, value)
            logger.debug(f"I2C send byte: addr=0x{address:02X} <- 0x{value:02X}")
        except Exception as e:
            raise I2CError(f"I2C send byte failed: addr=0x{address:02X}: {e}")

    def receive_byte(self, address: int) -> int:
        """
        Receive a single byte without a register address (SMBus Receive Byte).

        Args:
            address: I2C device address (7-bit)

        Returns:
            Byte value received

        Raises:
            I2CError: If receive operation fails
            I2CBusLockError: If lock cannot be acquired
        """
        if self.lock_enabled and self.lock:
            try:
                with self.lock:
                    return self._receive_byte_unlocked(address)
            except Timeout:
                raise I2CBusLockError(f"Failed to acquire I2C bus lock within {self.lock_timeout}s")
        else:
            return self._receive_byte_unlocked(address)

    def _receive_byte_unlocked(self, address: int) -> int:
        """Internal receive byte operation without locking."""
        try:
            time.sleep(READ_DELAY_MS / 1000.0)
            value = self.bus.read_byte(address)
            logger.debug(f"I2C receive byte: addr=0x{address:02X} -> 0x{value:02X}")
            return value
        except Exception as e:
            raise I2CError(f"I2C receive byte failed: addr=0x{address:02X}: {e}")

    def close(self) -> None:
        """Close the I2C bus connection."""
        if self.bus:
            self.bus.close()
            logger.debug(f"I2C bus {self.bus_number} closed")

    def __enter__(self) -> "I2CBus":
        """Context manager entry."""
        return self

    def __exit__(
        self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Optional[Any]
    ) -> bool:
        """Context manager exit."""
        self.close()
        return False
