# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Cellgain Ventus** - Production-ready I2C fan controller system for embedded Linux platforms. Provides fan speed control, RPM monitoring, and temperature sensing capabilities.

**Hardware:** [TBD - Add board name and specifications]

**Target Platform:** Multiplatform Linux (Banana Pi, Raspberry Pi, generic Linux systems with I2C support)

**Current Phase:** Phase 1 - Core Driver Development

## Development Commands

### Driver Testing

```bash
# Run basic I2C communication test
PYTHONPATH=. python3 tests/test_i2c_basic.py

# Test fan speed control
PYTHONPATH=. python3 examples/python/test_fan_control.py

# Test RPM monitoring
PYTHONPATH=. python3 examples/python/test_rpm_monitor.py
```

### I2C Device Verification

```bash
# Verify I2C devices are detected
i2cdetect -y [bus_number]

# Should show fan controller device(s) at configured addresses
```

### Installation

```bash
# Install in development mode
pip3 install -e .

# Install with gRPC support
pip3 install -e ".[grpc]"

# Install development dependencies
pip3 install -e ".[dev]"
```

## Architecture

### Layer Structure

```
┌─────────────────────────────────────────┐
│   High-Level API (TBD)                  │  <- API Layer (gRPC/REST)
│   - Fan control service                 │
│   - Monitoring endpoints                │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│   Fan Controller Driver                 │  <- Hardware Abstraction
│   - Speed control                       │
│   - RPM monitoring                      │
│   - Temperature sensing                 │
│   - Configuration management            │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│   I2C Communication (driver/i2c.py)     │  <- Low-level I/O
│   - Direct I2C read/write               │
│   - Cross-process bus locking           │
│   - Error handling                      │
└─────────────────────────────────────────┘
```

### Critical Design Patterns

**1. I2C Bus Locking**
- **Purpose**: Prevents conflicts when multiple processes share the I2C bus
- **Implementation**: File-based advisory locks using `filelock` library
- **Lock file**: `/var/lock/i2c-[bus].lock` (configurable)
- **Timeout**: 5 seconds (default, configurable)
- **Wraps every I2C read/write operation** in `ventus/driver/i2c.py`

**2. Thread Safety**
- Device-level locks for concurrent access
- Thread-safe configuration management
- Safe shutdown procedures

**3. Error Handling**
- Comprehensive I2C error detection
- Hardware fault monitoring
- Graceful degradation

**4. Configuration System**
- YAML/TOML-based configuration
- Auto-creation with sensible defaults
- Runtime configuration updates
- Per-device settings

## Important Files

### Core Hardware Interface
- `ventus/driver/i2c.py` - Low-level I2C communication with cross-process bus locking
- `ventus/driver/[chip].py` - Main fan controller driver (chip-specific)
- `ventus/driver/constants.py` - Hardware constants (addresses, registers, timing)

### Configuration
- `ventus/settings.py` - Configuration dataclasses and file loading
- `config/ventus.yaml` - Default configuration template

### Documentation
- `docs/hardware/` - Datasheets, schematics, integration guides
- `docs/development/` - Implementation notes and decisions
- `README.md` - Project overview and quick start

## Device Constraints

### Hardware Limitations
- **I2C bus speed**: Typically 100 kHz or 400 kHz (check device requirements)
- **No hot-plug**: Devices must be present at initialization
- **Chip-specific limitations**: [TBD - Add specific chip constraints]

### I2C Bus Sharing
- **Multiple services may use the same I2C bus** - always use I2C locking
- Follow the pattern established in the luminex project
- See `ventus/driver/i2c.py` for implementation reference

## Common Patterns

### Adding New Features

1. **New I2C register operations**: Add to appropriate driver file in `ventus/driver/`
2. **New configuration options**: Add to `ventus/settings.py` with validation
3. **New examples**: Add to `examples/python/` with clear documentation
4. **New tests**: Add to `tests/` following existing test patterns

### Working with I2C

```python
from ventus.driver.i2c import I2CBus

# Initialize I2C bus with locking
bus = I2CBus(bus_number=0, lock_enabled=True)

# Read byte from register (automatically locked)
value = bus.read_byte(device_address, register)

# Write byte to register (automatically locked)
bus.write_byte(device_address, register, value)
```

### Error Handling

```python
try:
    fan.set_speed(75)
except I2CError as e:
    # Handle I2C communication errors
    logger.error(f"I2C error: {e}")
except FanControllerError as e:
    # Handle fan controller specific errors
    logger.error(f"Fan controller error: {e}")
```

## Testing Strategy

### Hardware-Dependent Tests
Most tests require actual hardware with the fan controller connected:
- Tests expect specific I2C addresses (configurable via environment variables)
- Use `TEST_I2C_BUS` and `TEST_DEVICE_ADDRESS` environment variables

### Test Categories
- `test_i2c_*.py` - I2C communication validation
- `test_fan_*.py` - Fan control functionality
- `test_config_*.py` - Configuration management
- Integration tests require real hardware

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_i2c_basic.py -v

# Run with hardware address override
TEST_I2C_BUS=1 TEST_DEVICE_ADDRESS=0x2F pytest tests/
```

## Deployment

### To Target System (e.g., Banana Pi)

```bash
# Create deployment tarball
tar czf /tmp/ventus-deploy.tar.gz ventus/ requirements.txt setup.py tests/ examples/

# Copy to target system
scp /tmp/ventus-deploy.tar.gz user@target:/tmp/

# Install on target
ssh user@target "cd /opt && tar xzf /tmp/ventus-deploy.tar.gz && pip3 install -r requirements.txt"
```

### Systemd Service (TBD)

Will be added in Phase 2 for automatic startup and monitoring.

## Known Issues and Gotchas

### I2C Permissions
User must have permissions to access I2C devices:
```bash
# Add user to i2c group
sudo usermod -aG i2c username

# Or set permissions on device
sudo chmod 666 /dev/i2c-*
```

### I2C Lock File Permissions
Lock file directory must be writable:
```bash
sudo mkdir -p /var/lock
sudo chmod 1777 /var/lock
```

### Bus Speed Configuration
Some devices require specific I2C bus speeds. Configure via device tree or kernel module parameters.

## Development Phases

### Phase 1: Core Driver (Current)
- ✅ Project structure and templates
- 🔄 I2C communication layer
- 🔄 Fan controller driver implementation
- 🔄 Basic examples and tests

### Phase 2: Advanced Features (Planned)
- gRPC API (optional)
- Automatic fan curves (temperature-based)
- PID controller implementation
- Systemd service integration

### Phase 3: Tools & Monitoring (Planned)
- CLI client
- Web dashboard
- Real-time monitoring
- Logging and diagnostics

## Code Style Standards

### Python Standards
- **PEP 8**: Follow standard Python style guide
- **Type hints**: Use type annotations for function signatures
- **Docstrings**: Google-style docstrings for all public functions/classes
- **Line length**: Max 100 characters
- **Imports**: Group stdlib, third-party, local with blank lines between

### Documentation
- All public APIs must have comprehensive docstrings
- Include usage examples in docstrings
- Document hardware-specific behavior
- Add inline comments for complex logic

### Error Handling
- Always wrap errors with context
- Use custom exception types for different error categories
- Log errors appropriately (debug, info, warning, error)
- Never silently catch exceptions

## Hardware Integration Notes

### I2C Communication
- Always use the I2C locking mechanism from `ventus/driver/i2c.py`
- Handle I2C timeouts and retry logic
- Validate register addresses and values
- Check device presence before operations

### Fan Controller Operations
- Respect minimum/maximum speed limits
- Validate RPM readings for sanity
- Handle missing tachometer signals gracefully
- Monitor for hardware faults

### Temperature Sensing
- Validate temperature readings (reasonable range)
- Handle sensor errors
- Provide calibration options if needed

## Reference Projects

This project follows patterns established in:
- **bananapi-i2c-led-board (luminex)** - I2C driver architecture, gRPC API patterns
- **go-cyacd** - Professional code structure, documentation standards

## Quick Reference

### Essential Commands
```bash
# Check I2C devices
i2cdetect -y 0

# Test basic communication
python3 -m ventus.driver.test_basic

# Run examples
python3 examples/python/test_fan_control.py

# Install in dev mode
pip3 install -e .
```

### Configuration Locations
- **User config**: `~/.config/ventus/ventus.yaml`
- **System config**: `/etc/ventus/ventus.yaml`
- **Lock files**: `/var/lock/i2c-*.lock`

## Summary for AI Assistants

When working with this codebase:

1. **Follow luminex patterns** - I2C communication, locking, configuration
2. **Professional code quality** - Type hints, docstrings, error handling
3. **Hardware safety first** - Validate inputs, handle faults, safe defaults
4. **Document everything** - Especially hardware-specific behavior
5. **Test thoroughly** - Include hardware tests and edge cases
6. **Respect I2C locking** - Always use the locking mechanism
7. **Multiplatform support** - Don't assume specific hardware

**Critical Knowledge**:
- I2C bus locking is mandatory (follow luminex pattern)
- All register operations must validate addresses and values
- Fan speeds must be constrained to safe ranges
- RPM monitoring requires proper tachometer signal handling
- Temperature readings need validation and calibration
