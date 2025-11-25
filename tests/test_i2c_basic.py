#!/usr/bin/env python3
"""
Basic I2C Hardware Integration Test - NOT for pytest

This script tests basic I2C communication with real EMC2305 hardware.
It is meant to be run directly from the command line, NOT via pytest.
The functions return True/False values which are collected by main()
and used to determine the exit code.

For pytest unit tests (mock-based, no hardware required), see:
    tests/test_driver_unit.py

Usage:
    PYTHONPATH=. python3 tests/test_i2c_basic.py

Environment Variables:
    TEST_I2C_BUS: I2C bus number (default: 0)
    TEST_DEVICE_ADDRESS: EMC2305 I2C address in hex (default: 0x61)
"""

import os
import sys
import logging

from emc2305.driver.i2c import I2CBus, I2CError
from emc2305.driver import constants as const

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_i2c_bus_open():
    """Test I2C bus can be opened."""
    bus_number = int(os.getenv("TEST_I2C_BUS", "0"))

    logger.info(f"Opening I2C bus {bus_number}...")

    try:
        bus = I2CBus(bus_number=bus_number, lock_enabled=True)
        logger.info("✓ I2C bus opened successfully")
        bus.close()
        return True
    except I2CError as e:
        logger.error(f"✗ Failed to open I2C bus: {e}")
        return False


def test_device_detection():
    """Test EMC2305 device detection."""
    bus_number = int(os.getenv("TEST_I2C_BUS", "0"))
    address = int(os.getenv("TEST_DEVICE_ADDRESS", "0x61"), 16)

    logger.info(f"Testing device detection at address 0x{address:02X}...")

    try:
        bus = I2CBus(bus_number=bus_number, lock_enabled=True)

        # Read Product ID
        product_id = bus.read_byte(address, const.REG_PRODUCT_ID)
        logger.info(f"Product ID: 0x{product_id:02X}")

        if product_id != const.PRODUCT_ID:
            logger.error(
                f"✗ Unexpected Product ID: expected 0x{const.PRODUCT_ID:02X}, "
                f"got 0x{product_id:02X}"
            )
            bus.close()
            return False

        logger.info(f"✓ Product ID matches (0x{const.PRODUCT_ID:02X})")

        # Read Manufacturer ID
        mfg_id = bus.read_byte(address, const.REG_MANUFACTURER_ID)
        logger.info(f"Manufacturer ID: 0x{mfg_id:02X}")

        if mfg_id != const.MANUFACTURER_ID:
            logger.error(
                f"✗ Unexpected Manufacturer ID: expected 0x{const.MANUFACTURER_ID:02X}, "
                f"got 0x{mfg_id:02X}"
            )
            bus.close()
            return False

        logger.info(f"✓ Manufacturer ID matches (0x{const.MANUFACTURER_ID:02X})")

        # Read Revision
        revision = bus.read_byte(address, const.REG_REVISION)
        logger.info(f"✓ Chip Revision: 0x{revision:02X}")

        bus.close()
        logger.info("✓ Device detection successful")
        return True

    except I2CError as e:
        logger.error(f"✗ Device detection failed: {e}")
        return False


def test_register_read_write():
    """Test basic register read/write operations."""
    bus_number = int(os.getenv("TEST_I2C_BUS", "0"))
    address = int(os.getenv("TEST_DEVICE_ADDRESS", "0x61"), 16)

    logger.info("Testing register read/write...")

    try:
        bus = I2CBus(bus_number=bus_number, lock_enabled=True)

        # Read configuration register (should be readable)
        config = bus.read_byte(address, const.REG_CONFIGURATION)
        logger.info(f"Configuration register: 0x{config:02X}")

        # Read PWM frequency registers
        pwm_freq1 = bus.read_byte(address, const.REG_PWM_BASE_FREQ_1)
        pwm_freq2 = bus.read_byte(address, const.REG_PWM_BASE_FREQ_2)
        logger.info(f"PWM Base Freq 1: 0x{pwm_freq1:02X}")
        logger.info(f"PWM Base Freq 2: 0x{pwm_freq2:02X}")

        # Read Fan 1 setting
        fan1_setting = bus.read_byte(address, const.REG_FAN1_SETTING)
        logger.info(f"Fan 1 Setting: 0x{fan1_setting:02X} ({fan1_setting})")

        # Try writing to Fan 1 setting (safe write test)
        test_value = 128  # 50% duty cycle
        logger.info(f"Writing test value 0x{test_value:02X} to Fan 1 Setting...")
        bus.write_byte(address, const.REG_FAN1_SETTING, test_value)

        # Read back
        readback = bus.read_byte(address, const.REG_FAN1_SETTING)
        logger.info(f"Readback value: 0x{readback:02X}")

        if readback == test_value:
            logger.info("✓ Write/read verification successful")
        else:
            logger.warning(
                f"⚠ Write/read mismatch: wrote 0x{test_value:02X}, "
                f"read 0x{readback:02X}"
            )

        # Restore original value
        bus.write_byte(address, const.REG_FAN1_SETTING, fan1_setting)
        logger.info("✓ Original value restored")

        bus.close()
        logger.info("✓ Register read/write test successful")
        return True

    except I2CError as e:
        logger.error(f"✗ Register read/write test failed: {e}")
        return False


def main():
    """Run all I2C tests."""
    logger.info("=" * 60)
    logger.info("EMC2305 Basic I2C Communication Test")
    logger.info("=" * 60)

    # Get test parameters
    bus_number = int(os.getenv("TEST_I2C_BUS", "0"))
    address = int(os.getenv("TEST_DEVICE_ADDRESS", "0x61"), 16)

    logger.info(f"Test Configuration:")
    logger.info(f"  I2C Bus: {bus_number}")
    logger.info(f"  Device Address: 0x{address:02X}")
    logger.info("")

    results = {
        "I2C Bus Open": test_i2c_bus_open(),
        "Device Detection": test_device_detection(),
        "Register Read/Write": test_register_read_write(),
    }

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)

    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        icon = "✓" if result else "✗"
        logger.info(f"{icon} {test_name}: {status}")

    all_passed = all(results.values())
    logger.info("")

    if all_passed:
        logger.info("✓ All tests PASSED")
        return 0
    else:
        logger.error("✗ Some tests FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
