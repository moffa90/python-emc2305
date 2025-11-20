# EMC2305 Driver Examples

Example scripts demonstrating how to use the microchip-emc2305 Python driver.

## Prerequisites

```bash
# Install from PyPI
pip3 install microchip-emc2305

# Or install from source
cd /path/to/emc2305-python
pip3 install -e .
```

## Available Examples

### test_fan_control.py
Basic PWM control demonstration.
- Direct duty cycle control (0-100%)
- Ramp up/down examples
- Safe shutdown

**Usage:**
```bash
python3 test_fan_control.py
```

### test_rpm_monitor.py
RPM monitoring and tachometer reading.
- Real-time RPM display
- Status monitoring
- Continuous monitoring loop

**Usage:**
```bash
python3 test_rpm_monitor.py
```

### test_fsc_mode.py
Closed-loop FSC (Fan Speed Control) mode.
- PID-based RPM control
- Target RPM setting
- Hardware-controlled speed maintenance

**Usage:**
```bash
python3 test_fsc_mode.py
```

### test_fault_detection.py
Fault detection and status monitoring.
- Stall detection
- Spin failure detection
- Drive failure (aging fan) detection
- Alert handling

**Usage:**
```bash
python3 test_fault_detection.py
```

## Running Examples

### Method 1: Direct Execution
```bash
python3 test_fan_control.py
```

### Method 2: With PYTHONPATH
```bash
PYTHONPATH=../.. python3 test_fan_control.py
```

### Method 3: As Module
```bash
python3 -m examples.python.test_fan_control
```

## Hardware Requirements

- **Linux system** with I2C support
- **EMC2305 chip** (any variant: EMC2305-1/2/3/4)
- **At least one fan** connected to the EMC2305
- **I2C permissions** configured

## I2C Setup

### Check I2C Device
```bash
# Install i2c-tools
sudo apt-get install i2c-tools

# Scan I2C bus
i2cdetect -y 0

# You should see your EMC2305 device
```

### Set I2C Permissions
```bash
# Method 1: Add user to i2c group (recommended)
sudo usermod -aG i2c $USER
# Log out and back in for changes to take effect

# Method 2: Set permissions directly
sudo chmod 666 /dev/i2c-*
```

## Configuration

All examples use sensible defaults:
- **I2C Bus**: 0 (most common)
- **Device Address**: 0x61 (adjust in code for your hardware)

To customize, edit the configuration section at the top of each example:

```python
# Configuration
I2C_BUS = 0        # Your I2C bus number
DEVICE_ADDRESS = 0x61  # Your EMC2305 address
```

## Common I2C Addresses

The EMC2305 address depends on your hardware's ADDR_SEL pin configuration:

| ADDR_SEL | Address |
|----------|---------|
| GND      | 0x4C    |
| VDD      | 0x4D    |
| SDA      | 0x5C    |
| SCL      | 0x5D    |
| Float    | 0x5E/0x5F |

## Troubleshooting

### "Permission denied" on I2C
- Check I2C permissions (see I2C Setup above)
- Verify user is in `i2c` group: `groups $USER`

### "Device not found" error
- Verify hardware connection
- Check I2C address with `i2cdetect -y 0`
- Confirm correct bus number

### Fans not responding
- Check fan power supply
- Verify fan is connected to correct channel
- Ensure fan is compatible with PWM control
- Try increasing duty cycle above minimum

## Notes

- Examples include safety features (minimum duty cycles, safe shutdown)
- All examples are non-destructive and safe for hardware
- Code is documented with inline comments
- Adjust timing values as needed for your application

## Support

For issues or questions:
- Check the [main README](../../README.md)
- Review the [API documentation](../../README.md#api-documentation)
- Open an issue on GitHub
