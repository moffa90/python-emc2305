# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Nothing yet

## [1.1.0] - 2025-11-25

### Added
- `set_pwm_output_mode()` - Configure PWM output as open-drain or push-pull per channel
- `set_all_pwm_output_mode()` - Configure PWM output mode for all channels at once
- `get_pwm_output_mode()` - Read current PWM output mode for a channel
- `set_pwm_polarity()` - Configure PWM polarity (normal/inverted) per channel
- `get_pwm_polarity()` - Read current PWM polarity for a channel
- `MIN_VALID_RPM_READING` constant (200 RPM) for tachometer noise filtering

### Fixed
- **Critical**: PWM output mode register (0x2B) logic was inverted. Per datasheet: 0=open-drain (default), 1=push-pull. Previous implementation had this backwards.
- RPM readings below 200 RPM now return 0 (filters tachometer noise when fan is stopped)

## [1.0.0] - 2025-11-25

### Added
- PyPI publishing workflow with trusted publishing (OIDC)
- Donation section in README

### Changed
- Package published to PyPI as `microchip-emc2305`
- Removed phase/roadmap references from documentation

## [0.1.0] - 2025-11-24

### Added
- Initial release of python-emc2305 driver library
- Complete EMC2305 5-channel PWM fan controller support
- Dual control modes: PWM (direct duty cycle) and FSC (closed-loop RPM)
- Per-fan PWM frequency configuration
- RPM monitoring via tachometer
- Comprehensive fault detection (stall, spin failure, drive failure)
- SMBus Alert (ALERT#) hardware interrupt support
- Software configuration lock with race-condition safety
- Watchdog timer support
- Thread-safe operations with atomic register access
- Cross-process I2C bus locking using filelock
- YAML/TOML configuration file support
- Hardware capability auto-detection
- Full type hints (PEP 561) throughout codebase
- Comprehensive input validation (I2C addresses, registers, RPM bounds)
- Mock I2C bus implementation for hardware-independent testing
- 34 comprehensive unit tests with pytest
- Google-style docstrings for all public APIs
- Hardware-validated on EMC2305-1-APTR chip
- Example scripts for all major use cases
- Development documentation and hardware integration guides

### Fixed
- GLBL_EN bit now automatically enabled in driver initialization (critical for PWM output)
- UPDATE_TIME correctly set to 200ms (500ms breaks PWM control)
- Drive fail band register addresses corrected (datasheet errors)
- Minimum drive percentage unrestricted (0-100% range)
- PWM register readback quantization documented (25% reads as ~30%, physical output correct)

### Changed
- Configuration system uses sensible defaults with auto-creation
- PWM output configured as open-drain for better signal integrity
- PWM polarity set to normal (LOW=run) by default

### Documentation
- Complete README with quickstart and examples
- Hardware setup guide with I2C address configuration
- API documentation for all public classes and methods
- Production readiness status report
- Register readback behavior analysis
- Known limitations and platform requirements
- PyPI publishing guide

### Infrastructure
- Modern pyproject.toml configuration
- Backwards-compatible setup.py
- GitHub Actions CI/CD workflow
- Issue and pull request templates
- Contributing guidelines
- MIT License

[Unreleased]: https://github.com/moffa90/python-emc2305/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/moffa90/python-emc2305/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/moffa90/python-emc2305/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/moffa90/python-emc2305/releases/tag/v0.1.0
