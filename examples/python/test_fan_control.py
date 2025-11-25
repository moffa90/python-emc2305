#!/usr/bin/env python3
"""
Test Fan PWM Control

Basic example demonstrating direct PWM control of fans using the EMC2305 driver.

Usage:
    python3 examples/python/test_fan_control.py

Requirements:
    - EMC2305 device connected on I2C bus
    - At least one fan connected to Fan 1
    - Proper I2C permissions
"""

import time
import logging
from emc2305.driver.i2c import I2CBus
from emc2305.driver.emc2305 import EMC2305, ControlMode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Test basic PWM fan control."""
    logger.info("Starting PWM fan control test")

    try:
        # Initialize I2C bus
        logger.info("Initializing I2C bus...")
        i2c_bus = I2CBus(bus_number=0, lock_enabled=True)

        # Initialize EMC2305 fan controller
        logger.info("Initializing EMC2305...")
        fan_controller = EMC2305(
            i2c_bus=i2c_bus,
            device_address=0x61,
            use_external_clock=False,
            enable_watchdog=False,
            pwm_frequency=26000,
        )

        logger.info(
            f"EMC2305 detected: Product ID=0x{fan_controller.product_id:02X}, "
            f"Revision=0x{fan_controller.revision:02X}"
        )

        # Set Fan 1 to PWM control mode
        logger.info("Setting Fan 1 to PWM control mode")
        fan_controller.set_control_mode(1, ControlMode.PWM)

        # Test different PWM duty cycles
        duty_cycles = [30, 50, 75, 100, 75, 50, 30]

        for duty in duty_cycles:
            logger.info(f"Setting Fan 1 to {duty}% PWM duty cycle")
            fan_controller.set_pwm_duty_cycle(1, duty)

            # Read back the setting
            actual_duty = fan_controller.get_pwm_duty_cycle(1)
            logger.info(f"Fan 1 PWM duty cycle readback: {actual_duty:.1f}%")

            # Read RPM
            time.sleep(2)  # Wait for fan to stabilize
            rpm = fan_controller.get_current_rpm(1)
            logger.info(f"Fan 1 current RPM: {rpm}")

            # Check fan status
            status = fan_controller.get_fan_status(1)
            logger.info(f"Fan 1 status: {status}")

            time.sleep(3)

        # Set fan to safe idle speed
        logger.info("Setting Fan 1 to 40% for safe idle")
        fan_controller.set_pwm_duty_cycle(1, 40)

        logger.info("PWM control test completed successfully")

    except KeyboardInterrupt:
        logger.info("Test interrupted by user")

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)

    finally:
        logger.info("Cleaning up...")
        try:
            # Set fan to safe speed before exit
            fan_controller.set_pwm_duty_cycle(1, 30)
        except Exception:
            pass  # Ignore cleanup errors - fan_controller may not exist


if __name__ == "__main__":
    main()
