# EMC2305 Driver Tests

Test suite for the microchip-emc2305 Python driver.

## Overview

The test suite validates the EMC2305 driver functionality at multiple levels:
- I2C communication layer
- Driver logic and state management
- Hardware integration
- Fault detection and error handling

## Test Files

### test_i2c_basic.py
Basic I2C communication tests:
- Device detection
- Product/Manufacturer ID verification
- Read/write operations
- Cross-process locking

### test_emc2305_init.py
Driver initialization and configuration tests:
- Device initialization
- Configuration validation
- Channel configuration
- Control mode switching

## Running Tests

### Prerequisites

```bash
# Install test dependencies
pip install -e ".[dev]"

# Or install pytest directly
pip install pytest pytest-cov
```

### All Tests

```bash
# Run all tests
pytest tests/ -v

# Run with detailed output
pytest tests/ -vv

# Run specific test file
pytest tests/test_i2c_basic.py -v
```

### With Coverage

```bash
# Generate coverage report
pytest tests/ --cov=emc2305 --cov-report=term-missing

# Generate HTML coverage report
pytest tests/ --cov=emc2305 --cov-report=html
# Open htmlcov/index.html in browser
```

### Continuous Integration

```bash
# Run in CI mode (non-interactive)
pytest tests/ -v --tb=short
```

## Test Configuration

### Environment Variables

Configure hardware tests using environment variables:

```bash
# I2C bus number (default: 0)
export TEST_I2C_BUS=0

# EMC2305 I2C address (default: 0x61)
export TEST_DEVICE_ADDRESS=0x61

# Skip hardware tests (for CI/CD)
export TEST_SKIP_HARDWARE=true
```

### Example Test Run

```bash
# Test with custom hardware configuration
TEST_I2C_BUS=1 TEST_DEVICE_ADDRESS=0x4C pytest tests/ -v
```

## Hardware Requirements

Most tests require actual EMC2305 hardware:

- **Linux system** with I2C support
- **EMC2305 device** connected to I2C bus
- **Proper I2C permissions** configured
- **At least one fan** for full testing (optional)

### I2C Permissions

```bash
# Add user to i2c group
sudo usermod -aG i2c $USER

# Or set permissions
sudo chmod 666 /dev/i2c-*
```

### Verify Hardware

```bash
# Check I2C device is present
i2cdetect -y 0

# Should show device at configured address
```

## Test Categories

### ✅ Communication Tests
- I2C read/write operations
- Register access
- Cross-process locking
- Error handling

### ✅ Driver Tests
- Initialization sequence
- Configuration management
- PWM control
- RPM monitoring
- Fault detection

### ⏳ Future Tests (Planned)
- Mock hardware tests (for CI/CD)
- Performance benchmarks
- Stress tests
- Multi-device scenarios

## Writing Tests

### Test Structure

```python
import pytest
from emc2305.driver.i2c import I2CBus
from emc2305.driver.emc2305 import EMC2305

def test_basic_operation():
    """Test basic driver operation."""
    # Arrange
    i2c_bus = I2CBus(bus_number=0)
    controller = EMC2305(i2c_bus)

    # Act
    controller.set_pwm_duty_cycle(1, 50.0)

    # Assert
    duty = controller.get_pwm_duty_cycle(1)
    assert 45.0 <= duty <= 55.0  # Allow tolerance
```

### Test Markers (Future)

```python
@pytest.mark.hardware
def test_with_hardware():
    """Test requiring actual hardware."""
    pass

@pytest.mark.slow
def test_long_running():
    """Test that takes significant time."""
    pass
```

## Continuous Integration

For CI/CD environments without hardware:

```bash
# Skip hardware-dependent tests
TEST_SKIP_HARDWARE=true pytest tests/ -v

# Run only unit tests (when implemented)
pytest tests/ -v -m "not hardware"
```

## Troubleshooting

### "Device not found" Errors
- Verify hardware connection
- Check I2C address with `i2cdetect -y 0`
- Confirm correct bus number
- Check I2C permissions

### Permission Errors
- Ensure user is in `i2c` group
- Check `/dev/i2c-*` permissions
- May need to log out/in after adding user to group

### Timeout Errors
- Check I2C bus health
- Verify no conflicting processes
- Confirm hardware is powered

## Contributing Tests

When adding new tests:
1. Follow existing test structure
2. Include docstrings
3. Add hardware requirement notes
4. Update this README
5. Ensure tests pass on real hardware

## Test Coverage Goals

Target coverage metrics:
- **Overall**: 80%+
- **Critical paths**: 90%+
- **Error handling**: 85%+

Current coverage:
```bash
pytest tests/ --cov=emc2305 --cov-report=term
```

## Support

For test-related issues:
- Check test output carefully
- Review hardware connections
- Verify I2C configuration
- Open an issue with full test output
