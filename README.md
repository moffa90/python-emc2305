# microchip-emc2305

**Python Driver for Microchip EMC2305 5-Channel PWM Fan Controller**

A hardware-agnostic, production-ready Python driver for the Microchip EMC2305 fan controller with comprehensive feature support and robust I2C communication.

[![PyPI version](https://badge.fury.io/py/microchip-emc2305.svg)](https://badge.fury.io/py/microchip-emc2305)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/Platform-Linux-green.svg)](https://www.kernel.org/)
[![CI](https://github.com/moffa90/python-emc2305/workflows/CI/badge.svg)](https://github.com/moffa90/python-emc2305/actions)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Downloads](https://pepy.tech/badge/microchip-emc2305)](https://pepy.tech/project/microchip-emc2305)

---

## Features

### Hardware Support
- **Chip**: Microchip EMC2305-1, EMC2305-2, EMC2305-3, EMC2305-4 (5-channel variants)
- **Interface**: I2C/SMBus with cross-process locking
- **Platform**: Any Linux system with I2C support (Raspberry Pi, Banana Pi, x86, etc.)

### Fan Control
- ✅ **5 independent PWM channels** - Control up to 5 fans simultaneously
- ✅ **Dual control modes**:
  - **PWM Mode**: Direct duty cycle control (0-100%)
  - **FSC Mode**: Closed-loop RPM control with PID (500-32,000 RPM)
- ✅ **Per-fan PWM frequency** - Individual frequency control per channel
- ✅ **Configurable spin-up** - Aggressive start for high-inertia fans
- ✅ **RPM monitoring** - Real-time tachometer reading

### Advanced Features
- ✅ **Fault detection**: Stall, spin failure, aging fan detection
- ✅ **SMBus Alert (ALERT#)**: Hardware interrupt support
- ✅ **Software configuration lock** - Protect settings in production (race-condition safe)
- ✅ **Watchdog timer** - Automatic failsafe
- ✅ **Hardware capability detection** - Auto-detect chip features
- ✅ **Thread-safe operation** - Concurrent access protection with atomic operations
- ✅ **Comprehensive validation** - I2C addresses (0x00-0x7F), registers (0x00-0xFF), SMBus block limits (32 bytes), and RPM bounds checking

### Code Quality
- ✅ Full type hints (PEP 561)
- ✅ Comprehensive documentation
- ✅ Hardware-validated
- ✅ MIT licensed

---

## Installation

### From PyPI (Recommended)

```bash
pip install microchip-emc2305
```

### From Source

```bash
git clone https://github.com/moffa90/python-emc2305.git
cd emc2305-python
pip install -e .
```

### Optional Dependencies

```bash
# For YAML configuration file support
pip install microchip-emc2305[config]

# For development
pip install microchip-emc2305[dev]
```

---

## Quick Start

### Basic PWM Control

```python
from emc2305.driver.i2c import I2CBus
from emc2305.driver.emc2305 import EMC2305

# Initialize I2C bus (with cross-process locking)
i2c_bus = I2CBus(bus_number=0)

# Initialize EMC2305 at default address 0x61
fan_controller = EMC2305(i2c_bus, device_address=0x61)

# Set fan 1 to 75% duty cycle
fan_controller.set_pwm_duty_cycle(channel=1, percent=75.0)

# Read current RPM
rpm = fan_controller.get_current_rpm(channel=1)
print(f"Fan 1 speed: {rpm} RPM")
```

### Closed-Loop RPM Control (FSC Mode)

```python
from emc2305.driver.emc2305 import EMC2305, ControlMode, FanConfig

# Configure for FSC mode
config = FanConfig(
    control_mode=ControlMode.FSC,
    min_rpm=1000,
    max_rpm=4000,
    pid_gain_p=4,  # Proportional gain
    pid_gain_i=2,  # Integral gain
    pid_gain_d=1,  # Derivative gain
)

fan_controller.configure_fan(channel=1, config=config)
fan_controller.set_target_rpm(channel=1, rpm=3000)

# Hardware PID will maintain 3000 RPM automatically
```

### Fault Detection

```python
from emc2305.driver.emc2305 import FanStatus

# Check fan status
status = fan_controller.get_fan_status(channel=1)

if status == FanStatus.STALLED:
    print("Fan 1 is stalled!")
elif status == FanStatus.DRIVE_FAILURE:
    print("Fan 1 is aging (drive failure)")
elif status == FanStatus.OK:
    print("Fan 1 is operating normally")
```

### Alert/Interrupt Handling

```python
# Enable alerts for fan 1
fan_controller.configure_fan_alerts(channel=1, enabled=True)

# Check if any alerts are active
if fan_controller.is_alert_active():
    # Get which fans have alerts
    alerts = fan_controller.get_alert_status()
    for channel, has_alert in alerts.items():
        if has_alert:
            print(f"Fan {channel} has an alert condition")

    # Clear alert status
    fan_controller.clear_alert_status()
```

---

## Hardware Setup

### I2C Address Configuration

The EMC2305 I2C address is configurable via the ADDR_SEL pin:

| ADDR_SEL | Address |
|----------|---------|
| GND      | 0x4C    |
| VDD      | 0x4D    |
| SDA      | 0x5C    |
| SCL      | 0x5D    |
| Float    | 0x5E/0x5F |

Default in this driver: `0x61` (adjust for your hardware)

### I2C Bus Permissions

Ensure your user has I2C access:

```bash
# Add user to i2c group
sudo usermod -aG i2c $USER

# Or set permissions
sudo chmod 666 /dev/i2c-*
```

### Verify Hardware

```bash
# Install i2c-tools
sudo apt-get install i2c-tools

# Scan I2C bus 0
i2cdetect -y 0

# You should see your EMC2305 at its configured address
```

---

## Configuration File

Optional YAML configuration support:

```yaml
# ~/.config/emc2305/emc2305.yaml

i2c:
  bus: 0
  lock_enabled: true

emc2305:
  address: 0x61
  pwm_frequency_hz: 26000

  fans:
    1:
      name: "CPU Fan"
      control_mode: "fsc"
      min_rpm: 1000
      max_rpm: 4500
      default_target_rpm: 3000
      pid_gain_p: 4
      pid_gain_i: 2
      pid_gain_d: 1

    2:
      name: "Case Fan"
      control_mode: "pwm"
      default_duty_percent: 50
```

Load configuration:

```python
from emc2305.settings import ConfigManager

config_mgr = ConfigManager()
config = config_mgr.load()

# Use loaded configuration
fan_controller = EMC2305(
    i2c_bus,
    device_address=config.emc2305.address,
    pwm_frequency=config.emc2305.pwm_frequency_hz
)
```

---

## Architecture

```
┌─────────────────────────────────────┐
│   Application Code                  │
├─────────────────────────────────────┤
│   EMC2305 Driver (emc2305.py)       │  ← High-level API
│   - Fan control                     │
│   - RPM monitoring                  │
│   - Fault detection                 │
├─────────────────────────────────────┤
│   I2C Communication (i2c.py)        │  ← Low-level I/O
│   - SMBus operations                │
│   - Cross-process locking           │
├─────────────────────────────────────┤
│   Hardware (EMC2305 chip)           │
└─────────────────────────────────────┘
```

---

## API Documentation

### Main Classes

#### `EMC2305`
Main driver class for fan control.

**Methods:**
- `set_pwm_duty_cycle(channel, percent)` - Set PWM duty cycle
- `set_target_rpm(channel, rpm)` - Set target RPM (FSC mode)
- `get_current_rpm(channel)` - Read current RPM
- `get_fan_status(channel)` - Get fault status
- `configure_fan(channel, config)` - Apply full configuration
- `lock_configuration()` - Lock settings (irreversible until reset)
- `get_product_features()` - Read hardware capabilities

#### `FanConfig`
Configuration dataclass for fan channels.

**Fields:**
- `control_mode`: PWM or FSC
- `min_rpm`, `max_rpm`: RPM limits
- `min_drive_percent`: Minimum PWM percentage
- `pid_gain_p/i/d`: PID tuning parameters
- `spin_up_level_percent`, `spin_up_time_ms`: Spin-up configuration
- `pwm_divide`: Per-fan PWM frequency divider

#### `I2CBus`
Low-level I2C communication with locking.

**Methods:**
- `read_byte(address, register)`
- `write_byte(address, register, value)`
- `read_block(address, register, length)`
- `write_block(address, register, data)`

---

## Examples

See `examples/python/` directory:

- `test_fan_control.py` - Basic PWM control
- `test_rpm_monitor.py` - RPM monitoring
- `test_fsc_mode.py` - Closed-loop control
- `test_fault_detection.py` - Fault handling

---

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=emc2305 --cov-report=html

# Run specific test
pytest tests/test_emc2305_init.py -v
```

**Note:** Most tests require actual EMC2305 hardware.

---

## Compatibility

### Supported Python Versions
- Python 3.9+
- Python 3.10+
- Python 3.11+
- Python 3.12+

### Supported Platforms
- Linux (any distribution with I2C support)
- Raspberry Pi OS
- Banana Pi
- Generic embedded Linux

### Hardware Requirements
- I2C bus interface
- Microchip EMC2305 (any variant: EMC2305-1/2/3/4)
- Appropriate fan connectors and power supply

---

## Contributing

Contributions are welcome! This project aims to provide a comprehensive, hardware-agnostic driver for the EMC2305.

### Development Setup

```bash
git clone https://github.com/moffa90/python-emc2305.git
cd emc2305-python
pip install -e ".[dev]"
```

### Code Style

- Follow PEP 8
- Use type hints (PEP 484)
- Document all public APIs
- Run tests before submitting

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

Copyright (c) 2025 Contributors to the microchip-emc2305 project

---

## References

- [EMC2305 Datasheet](https://www.microchip.com/en-us/product/EMC2305)
- [SMBus Specification](http://smbus.org/specs/)
- [I2C-Tools Documentation](https://i2c.wiki.kernel.org/index.php/I2C_Tools)

---

## Support

- **Issues**: [GitHub Issues](https://github.com/moffa90/python-emc2305/issues)
- **Documentation**: [GitHub Wiki](https://github.com/moffa90/python-emc2305)
- **Discussions**: [GitHub Discussions](https://github.com/moffa90/python-emc2305/discussions)

---

## Donate

If you find this project useful, consider supporting its development:

[![PayPal](https://img.shields.io/badge/PayPal-Donate-blue.svg?logo=paypal)](https://paypal.me/moffax)

---

## Acknowledgments

This driver implements the complete EMC2305 register map and feature set as documented in the Microchip datasheet. Special thanks to the community contributors who helped validate and improve this driver.
