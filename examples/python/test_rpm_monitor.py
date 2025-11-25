#!/usr/bin/env python3
"""
Test RPM Monitoring

Example demonstrating real-time RPM monitoring from all fan channels.

Usage:
    python3 examples/python/test_rpm_monitor.py

Requirements:
    - EMC2305 device connected on I2C bus
    - Fans with tachometer output connected to channels
    - Proper I2C permissions
"""

import time
import logging
from emc2305.driver.i2c import I2CBus
from emc2305.driver.emc2305 import EMC2305, FanStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def format_rpm_display(channel: int, rpm: int, status: FanStatus) -> str:
    """Format RPM display with status indicator."""
    status_icon = {
        FanStatus.OK: "✓",
        FanStatus.STALLED: "✗ STALLED",
        FanStatus.SPIN_FAILURE: "✗ SPIN FAIL",
        FanStatus.DRIVE_FAILURE: "⚠ AGING",
        FanStatus.UNKNOWN: "?",
    }

    icon = status_icon.get(status, "?")
    return f"Fan {channel}: {rpm:5d} RPM  [{icon}]"


def main():
    """Monitor RPM from all fan channels."""
    logger.info("Starting RPM monitoring test")

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

        # Set all fans to 50% PWM for testing
        logger.info("Setting all fans to 50% PWM...")
        for channel in range(1, 6):
            try:
                fan_controller.set_pwm_duty_cycle(channel, 50)
            except Exception as e:
                logger.warning(f"Could not set Fan {channel}: {e}")

        # Wait for fans to stabilize
        logger.info("Waiting for fans to stabilize...")
        time.sleep(3)

        logger.info("\nStarting continuous RPM monitoring (Ctrl+C to stop)...")
        logger.info("=" * 60)

        # Continuous monitoring loop
        sample_count = 0
        while True:
            sample_count += 1

            # Read all fan states
            states = fan_controller.get_all_fan_states()

            # Display header every 10 samples
            if sample_count % 10 == 1:
                print("\n" + "=" * 60)
                print(f"Sample #{sample_count}")
                print("-" * 60)

            # Display RPM for each fan
            for channel in range(1, 6):
                state = states.get(channel)
                if state:
                    print(format_rpm_display(
                        channel,
                        state.current_rpm,
                        state.status
                    ))

            # Check watchdog status
            if fan_controller.check_watchdog():
                logger.warning("⚠ Watchdog timeout detected!")

            # Wait before next sample
            time.sleep(2)

    except KeyboardInterrupt:
        logger.info("\nMonitoring stopped by user")

    except Exception as e:
        logger.error(f"Monitoring failed: {e}", exc_info=True)

    finally:
        logger.info("Cleaning up...")


if __name__ == "__main__":
    main()
