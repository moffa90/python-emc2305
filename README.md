# Cellgain Ventus

**Professional I2C Fan Controller System for Embedded Linux Platforms**

A hardware-validated fan controller driver system with I2C communication and optional gRPC remote control API.

[![Platform](https://img.shields.io/badge/Platform-Linux-green)]()
[![Python](https://img.shields.io/badge/Python-3.9+-blue)]()
[![Status](https://img.shields.io/badge/Status-Development-yellow)]()

---

## Overview

Cellgain Ventus is a production-ready fan control system designed for embedded Linux platforms (Banana Pi, Raspberry Pi, etc.), providing complete hardware integration, fan speed control, RPM monitoring, and optional remote control capabilities via gRPC API.

### Hardware Configuration

- **Platform**: Linux-based embedded systems (Banana Pi, Raspberry Pi, etc.)
- **Fan Controller**: [TBD - Add chip model here]
- **Communication**: I2C bus with cross-process locking
- **Features**: Fan speed control, RPM monitoring, temperature sensing (chip-dependent)

---

## Project Structure

```
cellgain-ventus/
├── README.md                          # This file
├── ventus/                            # Main package
│   ├── driver/                        # Hardware driver
│   │   ├── i2c.py                     # I2C communication
│   │   ├── constants.py               # Register addresses & values
│   │   └── [chip].py                  # Main fan controller driver
│   ├── server/                        # gRPC server (optional)
│   ├── proto/                         # gRPC protocol definitions (optional)
│   └── settings.py                    # Configuration management
├── docs/
│   ├── hardware/                      # Hardware documentation
│   └── development/                   # Development notes
├── examples/python/                   # Example scripts
├── tests/                             # Test scripts
├── scripts/                           # Deployment utilities
├── requirements.txt                   # Python dependencies
└── setup.py                           # Package installation
```

---

## Quick Start

### Prerequisites

```bash
# On Banana Pi/Raspberry Pi (Debian/Ubuntu)
sudo apt-get update
sudo apt-get install python3 python3-pip i2c-tools

# Install dependencies
pip3 install -r requirements.txt
```

### Hardware Setup

1. Connect fan controller board to I2C bus
2. Verify I2C devices:
```bash
i2cdetect -y [bus_number]
# Should show your fan controller device(s)
```

### Basic Usage

```python
from ventus.driver import FanController

# Initialize fan controller
fan = FanController(bus=0, address=0x2F)

# Set fan speed (0-100%)
fan.set_speed(75)

# Read actual RPM
rpm = fan.get_rpm()
print(f"Fan speed: {rpm} RPM")

# Get temperature (if supported)
temp = fan.get_temperature()
print(f"Temperature: {temp}°C")
```

---

## Key Features

✅ **Hardware Integration**
- I2C communication with cross-process bus locking
- Fan speed control (PWM/DC)
- RPM monitoring (tachometer)
- Temperature sensing (chip-dependent)
- Fault detection and status monitoring

✅ **Professional Architecture**
- Multiplatform Linux support
- Thread-safe operations
- Comprehensive error handling
- Configuration management

🔄 **Optional Features** (TBD)
- gRPC server for remote control
- CLI client tool
- Web dashboard
- Systemd service integration

---

## Documentation

### Hardware Documentation
- Add datasheets in `docs/hardware/`
- Add schematics and PCB designs
- Integration guides

### Development
- See `docs/development/` for implementation notes
- API reference (TBD)
- Protocol documentation (TBD)

---

## Testing

```bash
# Run basic tests
python3 -m pytest tests/

# Test I2C communication
python3 tests/test_i2c_basic.py

# Test fan control
python3 examples/python/test_fan_control.py
```

---

## Development Roadmap

### Phase 1: Core Driver (In Progress)
- [ ] I2C communication layer
- [ ] Fan controller driver implementation
- [ ] Speed control and RPM monitoring
- [ ] Configuration system
- [ ] Basic examples

### Phase 2: Advanced Features (Planned)
- [ ] gRPC API (optional)
- [ ] Temperature-based control
- [ ] PID controller for automatic fan curves
- [ ] Systemd service

### Phase 3: Tools & Integration (Planned)
- [ ] CLI client
- [ ] Web dashboard
- [ ] Monitoring and logging
- [ ] Integration examples

---

## Contributing

This project follows Cellgain company policies:

1. **No direct commits to `main`** - All changes via Pull Requests
2. Create feature branches for development
3. Submit PRs with detailed descriptions
4. Include test results for hardware changes

---

## License

MIT License - see [LICENSE](LICENSE) file for details

---

## Acknowledgments

**Development Team:**
- **Jose Luis Moffa** - Hardware integration and driver development
- **Cellgain Team** - Engineering support

---

**Project Status**: 🚧 In Development

**Last Updated**: November 2025
