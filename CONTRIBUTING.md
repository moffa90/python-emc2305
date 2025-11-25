# Contributing to python-emc2305

Thank you for your interest in contributing to python-emc2305! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

Be respectful, constructive, and professional in all interactions. We're building a quality driver library together.

## How to Contribute

### Reporting Bugs

Before creating a bug report:
1. Check existing issues to avoid duplicates
2. Verify the bug with the latest version
3. Test with actual EMC2305 hardware if possible

Include in your bug report:
- **Description**: Clear description of the issue
- **Hardware**: EMC2305 variant, I2C address, platform (Raspberry Pi, Banana Pi, etc.)
- **Steps to reproduce**: Minimal code example
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Logs/Output**: Relevant error messages or I2C traces
- **Environment**: Python version, OS, I2C bus configuration

### Suggesting Features

Feature requests are welcome! Please include:
- **Use case**: Why is this feature needed?
- **Proposed solution**: How should it work?
- **Alternatives**: Other approaches considered
- **Hardware impact**: Does it require specific EMC2305 features?

### Pull Requests

#### Before You Start

1. Check existing issues and PRs to avoid duplicates
2. Discuss major changes in an issue first
3. Ensure you have hardware access for testing (or coordinate with maintainers)

#### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/python-emc2305.git
cd python-emc2305

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev,config]"

# Run tests
pytest tests/ -v
```

#### Code Standards

**Python Style**
- Follow PEP 8 style guide
- Maximum line length: 100 characters
- Use Black formatter: `black emc2305/ tests/`
- Use isort for imports: `isort emc2305/ tests/`

**Type Hints**
- All public functions must have type hints
- Use `typing` module types where appropriate
- Example:
  ```python
  def set_pwm_duty_cycle(self, channel: int, percent: float) -> None:
      """Set PWM duty cycle for a fan channel."""
  ```

**Documentation**
- Google-style docstrings for all public APIs
- Include parameters, return values, raises, examples
- Document hardware-specific behavior
- Example:
  ```python
  def get_current_rpm(self, channel: int) -> int:
      """
      Read current fan speed via tachometer.
      
      Args:
          channel: Fan channel (1-5)
          
      Returns:
          Current RPM (revolutions per minute)
          
      Raises:
          EMC2305ValidationError: If channel is invalid
          EMC2305CommunicationError: If I2C read fails
          
      Example:
          >>> rpm = controller.get_current_rpm(channel=1)
          >>> print(f"Fan 1: {rpm} RPM")
      """
  ```

**Error Handling**
- Use custom exception types from `emc2305.driver.emc2305`
- Always wrap errors with meaningful context
- Log appropriately (debug, info, warning, error)
- Never silently catch exceptions

**Testing**
- Add unit tests for new functionality
- Use mock I2C bus for hardware-independent tests
- Add hardware tests if new register operations added
- Aim for >80% code coverage
- All tests must pass before PR submission

#### Commit Messages

Follow conventional commits format:

```
type(scope): brief description

Longer description if needed, explaining the "why" not the "what".

- Bullet points for multiple changes
- Reference issues: Fixes #123
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions/modifications
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Maintenance tasks

**Examples:**
```
feat(driver): add hardware watchdog timer support

Implements watchdog configuration and monitoring for automatic
failsafe operation.

- Add watchdog enable/disable methods
- Add watchdog timeout configuration
- Add unit tests with mock hardware
- Update documentation with usage examples

Fixes #45
```

```
fix(i2c): handle I2C bus busy condition gracefully

Retry I2C operations up to 3 times with exponential backoff when
bus is busy, preventing spurious communication errors.

Fixes #67
```

#### Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Make your changes**
   - Follow code standards
   - Add tests
   - Update documentation
   - Run linters and tests locally

3. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat(scope): description"
   ```

4. **Push to your fork**
   ```bash
   git push origin feat/your-feature-name
   ```

5. **Create Pull Request**
   - Use the PR template
   - Link related issues
   - Describe changes clearly
   - Include test results
   - Add hardware test confirmation if applicable

6. **Code Review**
   - Address review feedback promptly
   - Keep discussion focused and constructive
   - Update PR based on feedback

7. **Merge**
   - Maintainer will merge when approved
   - Squash commits if requested
   - Delete branch after merge

#### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Type hints added for all new functions
- [ ] Google-style docstrings added
- [ ] Unit tests added and passing
- [ ] Hardware tested (or coordinated with maintainers)
- [ ] Documentation updated (README, docstrings, etc.)
- [ ] CHANGELOG.md updated
- [ ] No breaking changes (or documented/discussed)
- [ ] All CI checks passing

### Testing Guidelines

**Unit Tests (Required)**
- Use `tests/mock_i2c.py` for mocking hardware
- Test normal operation and edge cases
- Test error handling
- Verify input validation

**Hardware Tests (Optional but Encouraged)**
- Test with actual EMC2305 hardware
- Verify register operations with i2cdetect/i2cget
- Test with different fan types
- Verify PWM output with oscilloscope if possible

**Example Test Structure**
```python
def test_set_pwm_duty_cycle_valid(emc2305, mock_bus):
    """Test setting valid PWM duty cycle values."""
    test_values = [0.0, 25.0, 50.0, 75.0, 100.0]
    
    for percent in test_values:
        emc2305.set_pwm_duty_cycle(1, percent)
        
        # Verify register write
        pwm_reg = mock_bus.get_register(REG_FAN1_SETTING)
        expected = int((percent / 100.0) * 255)
        assert pwm_reg == expected

def test_set_pwm_duty_cycle_invalid(emc2305):
    """Test that invalid PWM values raise exceptions."""
    with pytest.raises(EMC2305ValidationError):
        emc2305.set_pwm_duty_cycle(1, -10.0)
    
    with pytest.raises(EMC2305ValidationError):
        emc2305.set_pwm_duty_cycle(1, 150.0)
```

### Documentation

**README Updates**
- Keep examples current
- Update feature lists
- Add new use cases

**Docstring Updates**
- Update when function signatures change
- Add examples for complex features
- Document hardware quirks

**Development Docs**
- Add findings to `docs/development/`
- Document hardware-specific behavior
- Explain design decisions

## Development Workflow

### Typical Contribution Flow

1. **Find/Create Issue**: Start with an issue describing the work
2. **Discuss Approach**: Get feedback before coding
3. **Fork & Branch**: Create feature branch
4. **Develop**: Write code, tests, docs
5. **Test Locally**: Run all tests and linters
6. **Hardware Test**: Test with real hardware if applicable
7. **Submit PR**: Create pull request with clear description
8. **Review**: Address feedback
9. **Merge**: Maintainer merges when approved

### Release Process (Maintainers)

1. Update version in `setup.py`, `pyproject.toml`, `emc2305/__init__.py`
2. Update `CHANGELOG.md` with release notes
3. Create git tag: `git tag -a v0.1.0 -m "Release 0.1.0"`
4. Push tag: `git push origin v0.1.0`
5. Build: `python -m build`
6. Publish to PyPI: `twine upload dist/*`
7. Create GitHub release with changelog

## Questions?

- **Issues**: https://github.com/moffa90/python-emc2305/issues
- **Discussions**: https://github.com/moffa90/python-emc2305/discussions
- **Email**: moffa3@gmail.com

Thank you for contributing to python-emc2305!
