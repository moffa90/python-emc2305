---
name: Bug Report
about: Report a bug or issue with python-emc2305
title: '[BUG] '
labels: bug
assignees: ''
---

## Bug Description
A clear and concise description of the bug.

## Hardware Setup
- **EMC2305 Variant**: (e.g., EMC2305-1-APTR, EMC2305-2, etc.)
- **I2C Address**: (e.g., 0x4D)
- **Platform**: (e.g., Raspberry Pi 4, Banana Pi M5, x86 Linux)
- **OS**: (e.g., Raspberry Pi OS Bookworm, Ubuntu 22.04)
- **Fan Type**: (e.g., Noctua NF-A4x10 PWM, Generic 4-wire fan)

## Software Environment
- **Python Version**: (e.g., 3.11.2)
- **python-emc2305 Version**: (e.g., 0.1.0)
- **Installation Method**: (pip, source, other)

## Steps to Reproduce
Minimal code example to reproduce the issue:

```python
from emc2305 import FanController

# Your code here
```

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened.

## Error Messages/Logs
```
Paste error messages, tracebacks, or logs here
```

## I2C Communication Traces (if applicable)
```bash
# Output of i2cdetect
$ i2cdetect -y 0

# Register reads/writes that failed
$ i2cget -y 0 0x4d 0x30 b
```

## Additional Context
Any other relevant information, hardware modifications, or observations.
