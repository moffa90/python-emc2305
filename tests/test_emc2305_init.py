#!/usr/bin/env python3
"""
EMC2305 Initialization Test

Tests EMC2305 driver initialization, configuration, and basic functionality.

Usage:
    PYTHONPATH=. python3 tests/test_emc2305_init.py

Environment Variables:
    TEST_I2C_BUS: I2C bus number (default: 0)
    TEST_DEVICE_ADDRESS: EMC2305 I2C address in hex (default: 0x61)
"""

import os
import sys
import logging
import time

from emc2305.driver.i2c import I2CBus
from emc2305.driver.emc2305 import EMC2305, EMC2305Error, EMC2305DeviceNotFoundError
from emc2305.driver import constants as const

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_driver_initialization():
    """Test EMC2305 driver can be initialized."""
    bus_number = int(os.getenv("TEST_I2C_BUS", "0"))
    address = int(os.getenv("TEST_DEVICE_ADDRESS", "0x61"), 16)

    logger.info(f"Initializing EMC2305 driver at 0x{address:02X}...")

    try:
        bus = I2CBus(bus_number=bus_number, lock_enabled=True)
        fan_controller = EMC2305(
            i2c_bus=bus,
            device_address=address,
            use_external_clock=False,
            enable_watchdog=False,
        )

        logger.info(
            f"✓ EMC2305 initialized: Product=0x{fan_controller.product_id:02X}, "
            f"Revision=0x{fan_controller.revision:02X}"
        )

        fan_controller.close()
        bus.close()
        return True

    except EMC2305DeviceNotFoundError as e:
        logger.error(f"✗ Device not found: {e}")
        return False

    except EMC2305Error as e:
        logger.error(f"✗ Initialization failed: {e}")
        return False


def test_fan_channels_accessible():
    """Test all 5 fan channels are accessible."""
    bus_number = int(os.getenv("TEST_I2C_BUS", "0"))
    address = int(os.getenv("TEST_DEVICE_ADDRESS", "0x61"), 16)

    logger.info("Testing fan channel accessibility...")

    try:
        bus = I2CBus(bus_number=bus_number, lock_enabled=True)
        fan_controller = EMC2305(
            i2c_bus=bus,
            device_address=address,
            use_external_clock=False,
        )

        # Test reading from all 5 channels
        for channel in range(1, const.NUM_FAN_CHANNELS + 1):
            duty = fan_controller.get_pwm_duty_cycle(channel)
            rpm = fan_controller.get_current_rpm(channel)
            status = fan_controller.get_fan_status(channel)

            logger.info(
                f"  Fan {channel}: Duty={duty:.1f}%, RPM={rpm}, Status={status.value}"
            )

        logger.info("✓ All fan channels accessible")

        fan_controller.close()
        bus.close()
        return True

    except Exception as e:
        logger.error(f"✗ Fan channel access test failed: {e}")
        return False


def test_pwm_control():
    """Test basic PWM control functionality."""
    bus_number = int(os.getenv("TEST_I2C_BUS", "0"))
    address = int(os.getenv("TEST_DEVICE_ADDRESS", "0x61"), 16)

    logger.info("Testing PWM control...")

    try:
        bus = I2CBus(bus_number=bus_number, lock_enabled=True)
        fan_controller = EMC2305(
            i2c_bus=bus,
            device_address=address,
        )

        # Test setting PWM on Fan 1
        test_duty = 50.0

        logger.info(f"Setting Fan 1 to {test_duty}% PWM...")
        fan_controller.set_pwm_duty_cycle(1, test_duty)

        time.sleep(0.5)

        # Read back
        actual_duty = fan_controller.get_pwm_duty_cycle(1)
        logger.info(f"Readback: {actual_duty:.1f}%")

        # Allow for small rounding errors
        if abs(actual_duty - test_duty) < 1.0:
            logger.info("✓ PWM control test passed")
            success = True
        else:
            logger.error(f"✗ PWM mismatch: set {test_duty}%, got {actual_duty:.1f}%")
            success = False

        # Restore safe speed
        fan_controller.set_pwm_duty_cycle(1, 30)

        fan_controller.close()
        bus.close()
        return success

    except Exception as e:
        logger.error(f"✗ PWM control test failed: {e}")
        return False


def test_rpm_reading():
    """Test RPM reading functionality."""
    bus_number = int(os.getenv("TEST_I2C_BUS", "0"))
    address = int(os.getenv("TEST_DEVICE_ADDRESS", "0x61"), 16)

    logger.info("Testing RPM reading...")

    try:
        bus = I2CBus(bus_number=bus_number, lock_enabled=True)
        fan_controller = EMC2305(
            i2c_bus=bus,
            device_address=address,
        )

        # Set Fan 1 to moderate speed
        fan_controller.set_pwm_duty_cycle(1, 50)
        time.sleep(2)  # Wait for fan to stabilize

        # Read RPM
        rpm = fan_controller.get_current_rpm(1)
        logger.info(f"Fan 1 RPM at 50%: {rpm}")

        # Check if RPM is reasonable (> 0 and < max)
        if 0 < rpm < const.MAX_RPM:
            logger.info("✓ RPM reading test passed")
            success = True
        elif rpm == 0:
            logger.warning("⚠ RPM is 0 - fan may not be connected or not spinning")
            success = False
        else:
            logger.warning(f"⚠ RPM reading seems unusual: {rpm}")
            success = False

        # Restore safe speed
        fan_controller.set_pwm_duty_cycle(1, 30)

        fan_controller.close()
        bus.close()
        return success

    except Exception as e:
        logger.error(f"✗ RPM reading test failed: {e}")
        return False


def test_configuration_persistence():
    """Test that configuration persists across operations."""
    bus_number = int(os.getenv("TEST_I2C_BUS", "0"))
    address = int(os.getenv("TEST_DEVICE_ADDRESS", "0x61"), 16)

    logger.info("Testing configuration persistence...")

    try:
        bus = I2CBus(bus_number=bus_number, lock_enabled=True)
        fan_controller = EMC2305(
            i2c_bus=bus,
            device_address=address,
        )

        # Set a specific configuration
        test_duty = 45.0
        fan_controller.set_pwm_duty_cycle(1, test_duty)

        # Read back immediately
        duty1 = fan_controller.get_pwm_duty_cycle(1)

        # Do some other operations
        fan_controller.get_current_rpm(1)
        fan_controller.get_fan_status(1)

        # Read again
        duty2 = fan_controller.get_pwm_duty_cycle(1)

        logger.info(f"Initial: {duty1:.1f}%, After operations: {duty2:.1f}%")

        # Check if values match
        if abs(duty1 - duty2) < 0.5:
            logger.info("✓ Configuration persistence test passed")
            success = True
        else:
            logger.error(f"✗ Configuration changed: {duty1:.1f}% -> {duty2:.1f}%")
            success = False

        # Restore safe speed
        fan_controller.set_pwm_duty_cycle(1, 30)

        fan_controller.close()
        bus.close()
        return success

    except Exception as e:
        logger.error(f"✗ Configuration persistence test failed: {e}")
        return False


def main():
    """Run all EMC2305 initialization tests."""
    logger.info("=" * 60)
    logger.info("EMC2305 Initialization Test Suite")
    logger.info("=" * 60)

    # Get test parameters
    bus_number = int(os.getenv("TEST_I2C_BUS", "0"))
    address = int(os.getenv("TEST_DEVICE_ADDRESS", "0x61"), 16)

    logger.info(f"Test Configuration:")
    logger.info(f"  I2C Bus: {bus_number}")
    logger.info(f"  Device Address: 0x{address:02X}")
    logger.info("")

    results = {
        "Driver Initialization": test_driver_initialization(),
        "Fan Channels Accessible": test_fan_channels_accessible(),
        "PWM Control": test_pwm_control(),
        "RPM Reading": test_rpm_reading(),
        "Configuration Persistence": test_configuration_persistence(),
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
