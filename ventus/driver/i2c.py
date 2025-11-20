"""
I2C Communication Layer

Provides low-level I2C communication with cross-process locking support.
Based on the architecture from cellgain-luminex project.
"""

import logging
import time
from pathlib import Path
from typing import Optional

try:
    import smbus2
except ImportError:
    smbus2 = None

from filelock import FileLock, Timeout

from ventus.driver.constants import (
    DEFAULT_I2C_BUS,
    DEFAULT_I2C_LOCK_TIMEOUT,
    DEFAULT_I2C_LOCK_PATH,
    READ_DELAY_MS,
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
                "smbus2 is required for I2C communication. "
                "Install with: pip install smbus2"
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

    def read_byte(self, address: int, register: int) -> int:
        """
        Read a single byte from a register.

        Args:
            address: I2C device address (7-bit)
            register: Register address

        Returns:
            Byte value read from register

        Raises:
            I2CError: If read operation fails
            I2CBusLockError: If lock cannot be acquired
        """
        if self.lock_enabled and self.lock:
            try:
                with self.lock:
                    return self._read_byte_unlocked(address, register)
            except Timeout:
                raise I2CBusLockError(
                    f"Failed to acquire I2C bus lock within {self.lock_timeout}s"
                )
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
            I2CError: If write operation fails
            I2CBusLockError: If lock cannot be acquired
        """
        if self.lock_enabled and self.lock:
            try:
                with self.lock:
                    self._write_byte_unlocked(address, register, value)
            except Timeout:
                raise I2CBusLockError(
                    f"Failed to acquire I2C bus lock within {self.lock_timeout}s"
                )
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
                raise I2CBusLockError(
                    f"Failed to acquire I2C bus lock within {self.lock_timeout}s"
                )
        else:
            return self._read_word_unlocked(address, register)

    def _read_word_unlocked(self, address: int, register: int) -> int:
        """Internal word read operation without locking."""
        try:
            time.sleep(READ_DELAY_MS / 1000.0)
            value = self.bus.read_word_data(address, register)
            logger.debug(f"I2C read word: addr=0x{address:02X} reg=0x{register:02X} -> 0x{value:04X}")
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
                raise I2CBusLockError(
                    f"Failed to acquire I2C bus lock within {self.lock_timeout}s"
                )
        else:
            self._write_word_unlocked(address, register, value)

    def _write_word_unlocked(self, address: int, register: int, value: int) -> None:
        """Internal word write operation without locking."""
        try:
            time.sleep(WRITE_DELAY_MS / 1000.0)
            self.bus.write_word_data(address, register, value)
            logger.debug(f"I2C write word: addr=0x{address:02X} reg=0x{register:02X} <- 0x{value:04X}")
        except Exception as e:
            raise I2CError(f"I2C word write failed: addr=0x{address:02X} reg=0x{register:02X}: {e}")

    def close(self) -> None:
        """Close the I2C bus connection."""
        if self.bus:
            self.bus.close()
            logger.debug(f"I2C bus {self.bus_number} closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
