# Hardware Documentation

This directory contains hardware-related documentation for the EMC2305 fan controller driver.

## Contents

Place the following documentation here:

### Datasheets
- Fan controller IC datasheet (PDF)
- Fan specifications
- Related component datasheets

### Schematics
- PCB schematics (PDF, source files)
- Board layout files
- BOM (Bill of Materials)

### Integration Guides
- Hardware setup instructions
- Connection diagrams
- Troubleshooting guides

## Hardware Specifications

**Fan Controller IC**: Microchip EMC2305 (5-channel PWM fan controller)

**I2C Addresses**: Configurable via ADDR_SEL pin (0x4C, 0x4D, 0x5C, 0x5D, 0x5E, 0x5F)

**Supported Features**:
- [x] Fan speed control (PWM)
- [x] RPM monitoring (tachometer)
- [x] Fault detection (stall, spin failure, drive failure)
- [x] Closed-loop RPM control (FSC mode with hardware PID)

**Electrical Specifications**:
- Operating voltage: 3.3V (VDD)
- I2C bus speed: 100 kHz / 400 kHz
- Fan power: 5V or 12V (separate rail)

## Quick Reference

### I2C Device Detection

```bash
# Scan I2C bus 0
i2cdetect -y 0

# Expected output should show EMC2305 at configured address (e.g., 0x4D)
```

## Notes

See the EMC2305 datasheet in this directory for complete hardware specifications.
