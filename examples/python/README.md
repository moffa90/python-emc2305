# Python Examples

Example scripts demonstrating how to use the Ventus fan controller driver.

## Prerequisites

```bash
# Install ventus package
pip3 install -e /path/to/cellgain-ventus

# Or add to PYTHONPATH
export PYTHONPATH=/path/to/cellgain-ventus:$PYTHONPATH
```

## Examples

### Basic Examples (Coming Soon)

- `basic_control.py` - Simple fan speed control
- `rpm_monitor.py` - Monitor fan RPM
- `temperature_control.py` - Temperature-based fan control
- `multi_fan.py` - Control multiple fans

## Running Examples

```bash
# Run with PYTHONPATH
PYTHONPATH=../.. python3 basic_control.py

# Or if installed
python3 basic_control.py
```

## Hardware Requirements

- Linux system with I2C support
- Fan controller board connected to I2C bus
- Proper permissions for I2C access

```bash
# Add user to i2c group
sudo usermod -aG i2c $USER

# Or set permissions
sudo chmod 666 /dev/i2c-*
```

## Notes

Examples assume:
- I2C bus 0 (default)
- Device address 0x2F (default)
- Adjust in code as needed for your hardware
