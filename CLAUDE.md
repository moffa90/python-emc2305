# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Cellgain Ventus** - Production-ready I2C fan controller system for embedded Linux platforms. Provides fan speed control, RPM monitoring, and temperature sensing capabilities.

**Hardware:**
- **Board:** CGW-LED-FAN-CTRL-4-REV1
- **Controller:** EMC2305-1-APTR (5-channel PWM fan controller)
- **I2C Address:** 0x4D (default)
- **Power Rails:** 3.3V (EMC2305 VDD), 5V (Fan power)

**Target Platform:** Multiplatform Linux (Banana Pi, Raspberry Pi, generic Linux systems with I2C support)

**Current Phase:** Phase 1 - Core Driver Development (Completed with critical fixes)

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
- **Wraps every I2C read/write operation** in `emc2305/driver/i2c.py`

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
- `emc2305/driver/i2c.py` - Low-level I2C communication with cross-process bus locking
- `emc2305/driver/[chip].py` - Main fan controller driver (chip-specific)
- `emc2305/driver/constants.py` - Hardware constants (addresses, registers, timing)

### Configuration
- `emc2305/settings.py` - Configuration dataclasses and file loading
- `config/emc2305.yaml` - Default configuration template

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
- See `emc2305/driver/i2c.py` for implementation reference

## Critical EMC2305 Configuration Requirements

⚠️ **IMPORTANT**: The following configuration settings are MANDATORY for EMC2305 to function correctly:

### 1. GLBL_EN Bit (Register 0x20, Bit 1) - CRITICAL
**Without this bit enabled, ALL PWM outputs are disabled regardless of individual fan settings.**

This is now automatically enabled in driver initialization (`emc2305/driver/emc2305.py:231-234`).

### 2. UPDATE_TIME - Must be 200ms
**Using 500ms breaks PWM control completely.**

Default is now correctly set to 200ms (`emc2305/driver/constants.py:589`, `emc2305/driver/emc2305.py:58`).

### 3. Drive Fail Band Registers - Corrected Addresses
**Some datasheets have incorrect register addresses.**

- `REG_FAN1_DRIVE_FAIL_BAND_LOW = 0x3A` (NOT 0x3B)
- `REG_FAN1_DRIVE_FAIL_BAND_HIGH = 0x3B` (NOT 0x3C)

### 4. PWM Voltage Levels - Hardware Consideration
⚠️ **EMC2305 outputs 3.3V PWM logic (VDD = 3.3V)**

If using 5V PWM fans, a hardware level shifter circuit is required (MOSFET-based or IC-based like TXB0104).

### 5. PWM Polarity - Fan-Specific
Different fans use different PWM logic:
- **Active Low (standard)**: LOW = run, HIGH = stop → Normal polarity
- **Active High (inverted)**: HIGH = run, LOW = stop → Inverted polarity

Check fan datasheet to determine correct configuration.

### 6. Minimum Drive - Unrestricted Range
`min_drive_percent: int = 0` (changed from 20% to allow full PWM range).

## Common Patterns

### Adding New Features

1. **New I2C register operations**: Add to appropriate driver file in `emc2305/driver/`
2. **New configuration options**: Add to `emc2305/settings.py` with validation
3. **New examples**: Add to `examples/python/` with clear documentation
4. **New tests**: Add to `tests/` following existing test patterns

### Working with I2C

```python
from emc2305.driver.i2c import I2CBus

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
- Always use the I2C locking mechanism from `emc2305/driver/i2c.py`
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
python3 -m emc2305.driver.test_basic

# Run examples
python3 examples/python/test_fan_control.py

# Install in dev mode
pip3 install -e .
```

### Configuration Locations
- **User config**: `~/.config/emc2305/emc2305.yaml`
- **System config**: `/etc/emc2305/emc2305.yaml`
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
