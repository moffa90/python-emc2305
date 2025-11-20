#!/usr/bin/env python3
"""
Test Fault Detection

Example demonstrating fault detection features including:
- Stall detection
- Spin-up failure detection
- Drive failure detection (aging fans)
- ALERT# pin status

Usage:
    python3 examples/python/test_fault_detection.py

Requirements:
    - EMC2305 device connected on I2C bus
    - Fans connected to test channels
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


def check_all_fan_faults(fan_controller: EMC2305) -> None:
    """Check and display fault status for all fans."""
    logger.info("\n" + "=" * 60)
    logger.info("Checking fault status for all fans...")
    logger.info("-" * 60)

    fault_detected = False

    for channel in range(1, 6):
        status = fan_controller.get_fan_status(channel)
        rpm = fan_controller.get_current_rpm(channel)
        duty = fan_controller.get_pwm_duty_cycle(channel)

        status_str = status.value.upper()

        if status == FanStatus.OK:
            icon = "✓"
        else:
            icon = "✗"
            fault_detected = True

        logger.info(
            f"{icon} Fan {channel}: {status_str:15s} | "
            f"RPM: {rpm:5d} | Duty: {duty:5.1f}%"
        )

    # Check watchdog
    if fan_controller.check_watchdog():
        logger.warning("⚠ Watchdog timeout detected!")
        fault_detected = True

    if not fault_detected:
        logger.info("✓ All fans operating normally")

    logger.info("=" * 60)


def simulate_stall_detection(fan_controller: EMC2305, channel: int) -> None:
    """
    Simulate stall detection by setting fan to very low speed.

    Note: In a real scenario, a stalled fan would trigger the fault automatically.
    This is for demonstration purposes only.
    """
    logger.info(f"\n--- Testing Stall Detection on Fan {channel} ---")

    logger.info(f"Setting Fan {channel} to normal speed (50%)...")
    fan_controller.set_pwm_duty_cycle(channel, 50)
    time.sleep(3)

    rpm = fan_controller.get_current_rpm(channel)
    logger.info(f"Fan {channel} RPM at 50%: {rpm}")

    logger.info(f"Reducing Fan {channel} to minimum speed (20%)...")
    fan_controller.set_pwm_duty_cycle(channel, 20)
    time.sleep(3)

    rpm = fan_controller.get_current_rpm(channel)
    status = fan_controller.get_fan_status(channel)
    logger.info(f"Fan {channel} RPM at 20%: {rpm}")
    logger.info(f"Fan {channel} status: {status.value}")

    if status == FanStatus.STALLED:
        logger.warning(f"✗ Fan {channel} stall detected!")
    elif rpm < 500:
        logger.info(f"⚠ Fan {channel} RPM is very low ({rpm}) but not stalled yet")
    else:
        logger.info(f"✓ Fan {channel} operating normally")


def main():
    """Test fault detection features."""
    logger.info("Starting fault detection test")

    try:
        # Initialize I2C bus
        logger.info("Initializing I2C bus...")
        i2c_bus = I2CBus(bus_number=0, lock_enabled=True)

        # Initialize EMC2305 fan controller with alerts enabled
        logger.info("Initializing EMC2305 with alerts enabled...")
        fan_controller = EMC2305(
            i2c_bus=i2c_bus,
            device_address=0x61,
            use_external_clock=False,
            enable_watchdog=False,
        )

        logger.info(
            f"EMC2305 detected: Product ID=0x{fan_controller.product_id:02X}, "
            f"Revision=0x{fan_controller.revision:02X}"
        )

        # Initial fault check
        logger.info("\n=== Initial Fault Status Check ===")
        check_all_fan_faults(fan_controller)

        # Set all fans to moderate speed
        logger.info("\n=== Setting All Fans to 50% ===")
        for channel in range(1, 6):
            try:
                fan_controller.set_pwm_duty_cycle(channel, 50)
                logger.info(f"Fan {channel} set to 50%")
            except Exception as e:
                logger.warning(f"Could not set Fan {channel}: {e}")

        time.sleep(3)

        # Check faults after startup
        logger.info("\n=== Fault Status After Startup ===")
        check_all_fan_faults(fan_controller)

        # Test stall detection on Fan 1 (if available)
        logger.info("\n=== Testing Stall Detection ===")
        logger.info("Note: This test attempts to detect low RPM conditions.")
        logger.info("Actual stall detection depends on fan characteristics.")

        simulate_stall_detection(fan_controller, 1)

        # Restore normal operation
        logger.info("\n=== Restoring Normal Operation ===")
        for channel in range(1, 6):
            try:
                fan_controller.set_pwm_duty_cycle(channel, 50)
            except:
                pass

        time.sleep(3)

        # Final fault check
        logger.info("\n=== Final Fault Status Check ===")
        check_all_fan_faults(fan_controller)

        # Monitor faults continuously for a short period
        logger.info("\n=== Continuous Fault Monitoring (30 seconds) ===")
        logger.info("Monitoring for any faults... (Ctrl+C to stop early)")

        start_time = time.time()
        while time.time() - start_time < 30:
            check_all_fan_faults(fan_controller)
            time.sleep(5)

        logger.info("\nFault detection test completed successfully")

    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)

    finally:
        logger.info("Cleaning up...")
        try:
            # Set all fans to safe speed
            for channel in range(1, 6):
                try:
                    fan_controller.set_pwm_duty_cycle(channel, 40)
                except:
                    pass
        except:
            pass


if __name__ == "__main__":
    main()
