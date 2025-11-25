# EMC2305 Driver User Guide

This guide provides comprehensive instructions for using the `microchip-emc2305` Python library to control PWM fans with the Microchip EMC2305 fan controller.

## Table of Contents

1. [Installation](#installation)
2. [Basic Usage](#basic-usage)
3. [Tachometer Configuration](#tachometer-configuration)
4. [Control Modes](#control-modes)
5. [Fault Detection](#fault-detection)
6. [Configuration Options](#configuration-options)
7. [Troubleshooting](#troubleshooting)

---

## Installation

### From PyPI

```bash
pip install microchip-emc2305
```

### From Source

```bash
git clone https://github.com/moffa90/python-emc2305.git
cd python-emc2305
pip install -e .
```

### System Requirements

- Python 3.9 or later
- Linux with I2C support
- I2C permissions (add user to `i2c` group or use `chmod 666 /dev/i2c-*`)

---

## Basic Usage

### Initializing the Controller

```python
from emc2305.driver.i2c import I2CBus
from emc2305.driver.emc2305 import EMC2305, FanConfig

# Create I2C bus connection (bus 0 is common on Raspberry Pi/Banana Pi)
bus = I2CBus(bus_number=0)

# Create EMC2305 controller instance
# Common addresses: 0x4C, 0x4D, 0x5C, 0x5D (depends on ADDR_SEL pin)
controller = EMC2305(i2c_bus=bus, device_address=0x4D)
```

### Setting Fan Speed (PWM Mode)

```python
# Set fan 1 to 50% speed
controller.set_pwm_duty_cycle(1, 50.0)

# Set fan 1 to 100% speed
controller.set_pwm_duty_cycle(1, 100.0)

# Turn off fan 1
controller.set_pwm_duty_cycle(1, 0.0)
```

### Reading Fan Speed (RPM)

```python
# Read current RPM from fan 1
rpm = controller.get_current_rpm(1)
print(f"Fan 1 is running at {rpm} RPM")
```

### Closing the Connection

```python
# Always close when done
controller.close()
```

---

## Tachometer Configuration

### Why Configuration Matters

The EMC2305 calculates RPM based on the number of tachometer pulses per revolution. Different fans produce different numbers of pulses:

| Fan Type | Pulses/Rev | `edges` Setting | Common Use Case |
|----------|------------|-----------------|-----------------|
| 1-pole   | 1          | `edges=3`       | High-speed server fans |
| 2-pole   | 2          | `edges=5`       | Standard PC fans (default) |
| 3-pole   | 3          | `edges=7`       | Some industrial fans |
| 4-pole   | 4          | `edges=9`       | Server/datacenter fans |

### Configuring the Tachometer

```python
from emc2305.driver.emc2305 import FanConfig

# For a 1-pulse-per-revolution fan
config = FanConfig(edges=3)
controller.configure_fan(1, config)

# Now RPM readings will be accurate
rpm = controller.get_current_rpm(1)
```

### Finding the Correct `edges` Value

If you don't know your fan's pulse count:

```python
import time

# Set fan to 100% and test different configurations
controller.set_pwm_duty_cycle(1, 100)
time.sleep(3)  # Wait for fan to reach full speed

print("Testing different edges configurations:")
for edges in [3, 5, 7, 9]:
    config = FanConfig(edges=edges)
    controller.configure_fan(1, config)
    time.sleep(0.5)
    rpm = controller.get_current_rpm(1)
    print(f"  edges={edges}: {rpm} RPM")

# Compare with your fan's rated RPM from the datasheet
# The matching configuration will give the closest value
```

### Example Output

```
Testing different edges configurations:
  edges=3: 8421 RPM  ← If fan is rated ~9000 RPM, this is correct
  edges=5: 4295 RPM
  edges=7: 11925 RPM
  edges=9: 5065 RPM
```

---

## Control Modes

### PWM Mode (Direct Control)

PWM mode gives you direct control over the fan's duty cycle:

```python
# Simple duty cycle control
controller.set_pwm_duty_cycle(1, 75.0)  # 75% speed

# Read back the current duty cycle
duty = controller.get_pwm_duty_cycle(1)
print(f"Duty cycle: {duty}%")
```

### FSC Mode (Closed-Loop RPM Control)

FSC (Fan Speed Control) mode uses the EMC2305's built-in PID controller to maintain a target RPM:

```python
from emc2305.driver.emc2305 import ControlMode, FanConfig

# Configure for FSC mode with PID parameters
config = FanConfig(
    control_mode=ControlMode.FSC,
    edges=3,  # Match your fan's tachometer
    min_rpm=1000,
    max_rpm=9000,
    pid_gain_p=4,  # Proportional gain (1, 2, 4, or 8)
    pid_gain_i=2,  # Integral gain (0, 1, 2, 4, 8, 16, or 32)
    pid_gain_d=1,  # Derivative gain (0, 1, 2, 4, 8, 16, or 32)
)

controller.configure_fan(1, config)

# Set target RPM - hardware PID will maintain this speed
controller.set_target_rpm(1, 5000)

# Check current speed
import time
time.sleep(2)  # Wait for PID to converge
rpm = controller.get_current_rpm(1)
print(f"Target: 5000 RPM, Actual: {rpm} RPM")
```

### Switching Between Modes

```python
from emc2305.driver.emc2305 import ControlMode

# Switch to PWM mode
controller.set_control_mode(1, ControlMode.PWM)
controller.set_pwm_duty_cycle(1, 50)

# Switch to FSC mode
controller.set_control_mode(1, ControlMode.FSC)
controller.set_target_rpm(1, 3000)
```

---

## Fault Detection

### Checking Fan Status

```python
from emc2305.driver.emc2305 import FanStatus

status = controller.get_fan_status(1)

if status == FanStatus.OK:
    print("Fan is running normally")
elif status == FanStatus.STALLED:
    print("Fan is stalled! Check for obstructions")
elif status == FanStatus.SPIN_FAILURE:
    print("Fan failed to spin up")
elif status == FanStatus.DRIVE_FAILURE:
    print("Fan is aging (can't reach target speed)")
```

### Monitoring All Fans

```python
# Get status of all fans
for channel in range(1, 6):
    status = controller.get_fan_status(channel)
    rpm = controller.get_current_rpm(channel)
    print(f"Fan {channel}: {status.name}, {rpm} RPM")
```

### Using Alerts

```python
# Enable alerts for a fan
controller.configure_fan_alerts(1, enabled=True)

# Check for active alerts
if controller.is_alert_active():
    alerts = controller.get_alert_status()
    for channel, has_alert in alerts.items():
        if has_alert:
            print(f"Alert on fan {channel}!")

    # Clear alerts after handling
    controller.clear_alert_status()
```

---

## Configuration Options

### FanConfig Parameters

```python
from emc2305.driver.emc2305 import FanConfig, ControlMode

config = FanConfig(
    # Control mode
    control_mode=ControlMode.PWM,  # or ControlMode.FSC

    # Tachometer configuration
    edges=5,  # 3, 5, 7, or 9 based on fan type

    # RPM limits (for FSC mode)
    min_rpm=500,
    max_rpm=16000,

    # PWM limits
    min_drive_percent=0,  # Minimum PWM (0-100)

    # PID gains (for FSC mode)
    pid_gain_p=2,   # Proportional: 1, 2, 4, 8
    pid_gain_i=1,   # Integral: 0, 1, 2, 4, 8, 16, 32
    pid_gain_d=1,   # Derivative: 0, 1, 2, 4, 8, 16, 32

    # Spin-up configuration
    spin_up_level_percent=50,  # Initial spin-up PWM
    spin_up_time_ms=500,       # Spin-up duration

    # Error range for FSC mode (±RPM window)
    error_range_rpm=0,  # 0, 50, 100, or 200

    # Glitch filtering
    glitch_filter_enabled=True,

    # Update time (control loop period)
    update_time_ms=200,  # 100, 200, 300, 400, 500, 800, 1200, 1600
)
```

### EMC2305 Initialization Options

```python
controller = EMC2305(
    i2c_bus=bus,
    device_address=0x4D,        # I2C address
    use_external_clock=False,   # Use internal 32kHz clock
    enable_watchdog=False,      # Enable watchdog timer
    pwm_frequency=26000,        # PWM base frequency in Hz
)
```

---

## Troubleshooting

### RPM Reads 0 or Very Low

1. **Check `edges` configuration** - Wrong edges setting gives wrong RPM
2. **Verify pull-up resistor** - TACH pins need 10kΩ pull-up to 3.3V
3. **Check wiring** - Ensure TACH wire is connected to correct channel

### RPM Readings Are Unstable

1. **Add glitch filtering**:
   ```python
   config = FanConfig(glitch_filter_enabled=True)
   ```
2. **Check for electrical noise** - Use shielded cables for long runs

### Fan Won't Spin

1. **Check minimum drive**:
   ```python
   config = FanConfig(min_drive_percent=20)  # Some fans need minimum PWM
   ```
2. **Increase spin-up level**:
   ```python
   config = FanConfig(spin_up_level_percent=75, spin_up_time_ms=1000)
   ```

### I2C Communication Errors

1. **Check address**: Use `i2cdetect -y 0` to find your device
2. **Check permissions**: Add user to `i2c` group
3. **Check wiring**: Verify SDA, SCL, and GND connections

### Device Not Found

```bash
# Scan I2C bus
sudo i2cdetect -y 0

# Expected output shows device at configured address:
#      0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
# 40: -- -- -- -- -- -- -- -- -- -- -- -- 4c 4d -- --
```

---

## Complete Example

```python
#!/usr/bin/env python3
"""Complete EMC2305 fan control example."""

from emc2305.driver.i2c import I2CBus
from emc2305.driver.emc2305 import EMC2305, FanConfig, ControlMode, FanStatus
import time

def main():
    # Initialize
    bus = I2CBus(bus_number=0)
    controller = EMC2305(i2c_bus=bus, device_address=0x4D)

    try:
        # Configure fan 1 for 1-pulse-per-revolution tachometer
        config = FanConfig(
            edges=3,
            control_mode=ControlMode.PWM,
            glitch_filter_enabled=True,
        )
        controller.configure_fan(1, config)

        # Run through different speeds
        for speed in [25, 50, 75, 100]:
            controller.set_pwm_duty_cycle(1, speed)
            time.sleep(2)

            rpm = controller.get_current_rpm(1)
            status = controller.get_fan_status(1)

            print(f"PWM: {speed}%, RPM: {rpm}, Status: {status.name}")

        # Check for any faults
        status = controller.get_fan_status(1)
        if status != FanStatus.OK:
            print(f"Warning: Fan status is {status.name}")

    finally:
        # Always clean up
        controller.close()

if __name__ == "__main__":
    main()
```

---

## Additional Resources

- [EMC2305 Datasheet](https://www.microchip.com/en-us/product/EMC2305)
- [Project GitHub Repository](https://github.com/moffa90/python-emc2305)
- [API Reference](README.md#api-documentation)
