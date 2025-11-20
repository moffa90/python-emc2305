# Hardware Documentation

This directory contains hardware-related documentation for the Cellgain Ventus fan controller.

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

**Fan Controller IC**: [TBD - Add chip model]

**I2C Addresses**: [TBD - List device addresses]

**Supported Features**:
- [ ] Fan speed control (PWM/DC)
- [ ] RPM monitoring (tachometer)
- [ ] Temperature sensing
- [ ] Fault detection

**Electrical Specifications**:
- Operating voltage: [TBD]
- I2C bus speed: [TBD]
- Fan power ratings: [TBD]

## Quick Reference

### I2C Device Detection

```bash
# Scan I2C bus 0
i2cdetect -y 0

# Expected output should show devices at:
# [TBD - List expected addresses]
```

### Pin Connections

[TBD - Add pinout diagram or table]

## Notes

Add any hardware-specific notes, quirks, or important considerations here.
