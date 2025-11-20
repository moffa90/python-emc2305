# Tests

Test suite for Ventus fan controller driver.

## Test Categories

### Unit Tests
- I2C communication layer tests
- Configuration management tests
- Driver logic tests (mocked hardware)

### Integration Tests
- Hardware communication tests (requires actual hardware)
- Multi-device tests
- Concurrent access tests

### System Tests
- End-to-end functionality tests
- Performance tests
- Stress tests

## Running Tests

### All Tests
```bash
pytest tests/ -v
```

### Specific Test Categories
```bash
# Unit tests only (no hardware required)
pytest tests/ -v -m "not hardware"

# Integration tests (requires hardware)
pytest tests/ -v -m hardware
```

### With Coverage
```bash
pytest tests/ --cov=ventus --cov-report=html
```

## Test Configuration

Set environment variables for hardware tests:

```bash
export TEST_I2C_BUS=0
export TEST_DEVICE_ADDRESS=0x2F
export TEST_SKIP_HARDWARE=true  # Skip hardware tests
```

## Hardware Test Requirements

Hardware tests require:
- Linux system with I2C support
- Fan controller board connected
- Proper I2C permissions
- Device at configured address

## Notes

- Most tests require actual hardware
- Mock tests will be added for CI/CD
- Integration tests may take longer to run
