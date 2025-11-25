## Description
Brief description of what this PR does.

Fixes #(issue number)

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Code refactoring
- [ ] Performance improvement
- [ ] Test addition/modification

## Hardware Tested
- [ ] Tested with actual EMC2305 hardware
- [ ] Hardware variant: (e.g., EMC2305-1-APTR)
- [ ] Platform: (e.g., Raspberry Pi 4)
- [ ] I2C address: (e.g., 0x4D)
- [ ] Fan type: (e.g., Noctua NF-A4x10 PWM)

OR

- [ ] No hardware testing required (docs/tests only)
- [ ] Hardware testing coordinated with maintainers

## Changes Made
- Change 1
- Change 2
- Change 3

## Testing Performed

### Unit Tests
```bash
# Test results
pytest tests/test_driver_unit.py -v
```

### Hardware Tests (if applicable)
```bash
# Commands run
i2cdetect -y 0
python3 examples/python/test_fan_control.py
```

**Test Results:**
- [ ] All unit tests pass
- [ ] Hardware tests pass (if applicable)
- [ ] No regressions observed

## Checklist
- [ ] Code follows project style guidelines (PEP 8, Black, isort)
- [ ] Type hints added for all new functions
- [ ] Google-style docstrings added
- [ ] Unit tests added and passing
- [ ] Hardware tested (or coordinated with maintainers)
- [ ] Documentation updated (README, docstrings, etc.)
- [ ] CHANGELOG.md updated
- [ ] No breaking changes (or documented in CHANGELOG)
- [ ] All CI checks passing
- [ ] Commit messages follow conventional commits format

## Additional Notes
Any additional information that reviewers should know.

## Screenshots/Oscilloscope Traces (if applicable)
If relevant, include oscilloscope traces of PWM signals, screenshots of monitoring tools, etc.
