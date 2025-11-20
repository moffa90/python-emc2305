#!/usr/bin/env python3
"""
Test FSC (Fan Speed Control) Mode

Example demonstrating closed-loop RPM control using the EMC2305's
built-in PID controller.

Usage:
    python3 examples/python/test_fsc_mode.py

Requirements:
    - EMC2305 device connected on I2C bus
    - At least one fan with tachometer connected to Fan 1
    - Proper I2C permissions
"""

import time
import logging
from emc2305.driver.i2c import I2CBus
from emc2305.driver.emc2305 import EMC2305, ControlMode, FanConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Test closed-loop RPM control."""
    logger.info("Starting FSC mode test")

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
        )

        logger.info(
            f"EMC2305 detected: Product ID=0x{fan_controller.product_id:02X}, "
            f"Revision=0x{fan_controller.revision:02X}"
        )

        # Configure Fan 1 for FSC mode with custom PID gains
        logger.info("Configuring Fan 1 for FSC mode...")
        fan_config = FanConfig(
            enabled=True,
            control_mode=ControlMode.FSC,
            min_rpm=1000,
            max_rpm=4000,
            min_drive_percent=20,
            update_time_ms=500,
            edges=5,  # 2-pole fan
            spin_up_level_percent=50,
            spin_up_time_ms=500,
            pid_gain_p=2,  # Moderate proportional gain
            pid_gain_i=1,  # Low integral gain
            pid_gain_d=1,  # Low derivative gain
        )

        fan_controller.configure_fan(1, fan_config)
        logger.info("Fan 1 configured for FSC mode with PID gains: P=2, I=1, D=1")

        # Test different target RPMs
        target_rpms = [2000, 2500, 3000, 3500, 3000, 2500, 2000]

        for target_rpm in target_rpms:
            logger.info(f"\nSetting target RPM to {target_rpm}")
            fan_controller.set_target_rpm(1, target_rpm)

            # Monitor convergence to target RPM
            logger.info("Monitoring RPM convergence (10 seconds)...")
            start_time = time.time()

            while time.time() - start_time < 10:
                current_rpm = fan_controller.get_current_rpm(1)
                target_readback = fan_controller.get_target_rpm(1)
                duty = fan_controller.get_pwm_duty_cycle(1)
                status = fan_controller.get_fan_status(1)

                error = abs(current_rpm - target_rpm)
                error_percent = (error / target_rpm * 100) if target_rpm > 0 else 0

                logger.info(
                    f"Target: {target_readback:4d} RPM | "
                    f"Current: {current_rpm:4d} RPM | "
                    f"Error: {error:4d} RPM ({error_percent:5.1f}%) | "
                    f"Duty: {duty:5.1f}% | "
                    f"Status: {status.value}"
                )

                # Check if converged (within 5%)
                if error_percent < 5.0:
                    logger.info(f"✓ Converged to target within 5% error")
                    break

                time.sleep(1)

            # Hold at this RPM for a moment
            time.sleep(2)

        # Return to idle speed
        logger.info("\nReturning to idle speed (1500 RPM)")
        fan_controller.set_target_rpm(1, 1500)
        time.sleep(5)

        logger.info("\nFSC mode test completed successfully")

    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)

    finally:
        logger.info("Cleaning up...")
        try:
            # Set fan to safe idle speed
            fan_controller.set_target_rpm(1, 1500)
        except:
            pass


if __name__ == "__main__":
    main()
