# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure
- Basic driver architecture
- I2C communication layer with cross-process locking
- Configuration management system
- 20+ documented hardware constants to replace magic numbers (REG_*, CONFIG_*, GAIN_*, etc.)
- Comprehensive I2C input validation for addresses (0x00-0x7F), registers (0x00-0xFF), and block lengths (max 32 bytes)
- RPM calculation bounds checking and measurement validation
- Thread-safe atomic operations for configuration locking
- SMBus protocol compliance with block operation limits

### Fixed
- Configuration lock race condition in EMC2305 initialization
- I2C parameter validation with clear error messages
- Tachometer reading validation reliability

### Changed
- Replaced all magic numbers with named constants from constants.py
- Enhanced error handling with context-specific validation messages
- Improved code maintainability through explicit constant usage

## [0.1.0] - TBD

### Added
- First release
