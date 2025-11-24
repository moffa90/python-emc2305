# PyPI Publishing Guide

This guide explains how to publish python-emc2305 to the Python Package Index (PyPI).

## Prerequisites

### 1. PyPI Account
- Create account at https://pypi.org/account/register/
- Verify your email address
- Set up Two-Factor Authentication (2FA) - **REQUIRED** for publishing

### 2. TestPyPI Account (for testing)
- Create account at https://test.pypi.org/account/register/
- This is separate from the main PyPI account

### 3. Install Build Tools
```bash
pip install --upgrade build twine
```

### 4. API Tokens (Recommended)
Generate API tokens instead of using passwords:

**For PyPI:**
1. Go to https://pypi.org/manage/account/token/
2. Create a token with scope limited to `python-emc2305` (after first upload)
3. Save token securely (you'll only see it once)

**For TestPyPI:**
1. Go to https://test.pypi.org/manage/account/token/
2. Create a token
3. Save token securely

### 5. Configure `.pypirc` (Optional but Recommended)
Create `~/.pypirc`:
```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR-API-TOKEN-HERE

[testpypi]
username = __token__
password = pypi-YOUR-TEST-API-TOKEN-HERE
```

**Important:** Set restrictive permissions:
```bash
chmod 600 ~/.pypirc
```

## Pre-Release Checklist

Before publishing, ensure:

- [ ] Version number updated in:
  - [ ] `setup.py`
  - [ ] `pyproject.toml`
  - [ ] `emc2305/__init__.py`
- [ ] `CHANGELOG.md` updated with release notes
- [ ] All tests passing: `pytest tests/ -v`
- [ ] Code quality checks passing:
  - [ ] `black --check emc2305/ tests/`
  - [ ] `isort --check-only emc2305/ tests/`
  - [ ] `ruff check emc2305/`
- [ ] Documentation up to date
- [ ] Git tag created: `git tag -a v0.1.0 -m "Release 0.1.0"`
- [ ] Changes committed and pushed to GitHub
- [ ] GitHub CI/CD passing

## Building the Package

### 1. Clean Previous Builds
```bash
rm -rf build/ dist/ *.egg-info
```

### 2. Build Distribution Files
```bash
python -m build
```

This creates:
- `dist/microchip-emc2305-0.1.0.tar.gz` (source distribution)
- `dist/microchip_emc2305-0.1.0-py3-none-any.whl` (wheel distribution)

### 3. Verify Package Contents
```bash
# Check tarball contents
tar -tzf dist/microchip-emc2305-0.1.0.tar.gz

# Check wheel contents
unzip -l dist/microchip_emc2305-0.1.0-py3-none-any.whl
```

### 4. Check Package Metadata
```bash
twine check dist/*
```

Expected output:
```
Checking dist/microchip-emc2305-0.1.0.tar.gz: PASSED
Checking dist/microchip_emc2305-0.1.0-py3-none-any.whl: PASSED
```

## Testing on TestPyPI

**Always test on TestPyPI before publishing to production PyPI!**

### 1. Upload to TestPyPI
```bash
twine upload --repository testpypi dist/*
```

Or with explicit URL:
```bash
twine upload --repository-url https://test.pypi.org/legacy/ dist/*
```

### 2. Test Installation from TestPyPI
```bash
# Create fresh virtual environment
python3 -m venv test-env
source test-env/bin/activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/     --extra-index-url https://pypi.org/simple/     microchip-emc2305

# Note: --extra-index-url allows dependencies to be installed from main PyPI
```

### 3. Verify Installation
```python
python3 << 'EOF'
import emc2305
print(f"Version: {emc2305.__version__}")
print(f"Author: {emc2305.__author__}")

# Test imports
from emc2305 import FanController, EMC2305, I2CBus
from emc2305 import ControlMode, FanStatus
print("All imports successful!")
EOF
```

### 4. Run Examples (if hardware available)
```bash
# Test basic functionality
PYTHONPATH=. python3 examples/python/test_fan_control.py
```

## Publishing to Production PyPI

### 1. Final Checks
- [ ] TestPyPI installation successful
- [ ] All imports working
- [ ] Version number is correct
- [ ] CHANGELOG.md is up to date
- [ ] Git tag pushed: `git push origin v0.1.0`

### 2. Upload to PyPI
```bash
twine upload dist/*
```

### 3. Verify Upload
1. Check PyPI page: https://pypi.org/project/microchip-emc2305/
2. Verify metadata, description, links
3. Check that badges work in README

### 4. Test Installation from PyPI
```bash
# Fresh virtual environment
python3 -m venv prod-test-env
source prod-test-env/bin/activate

# Install from PyPI
pip install microchip-emc2305

# Verify
python3 -c "import emc2305; print(emc2305.__version__)"
```

### 5. Create GitHub Release
1. Go to https://github.com/moffa90/python-emc2305/releases
2. Click "Draft a new release"
3. Select tag: `v0.1.0`
4. Title: `v0.1.0 - Initial Release`
5. Copy release notes from `CHANGELOG.md`
6. Attach distribution files (optional)
7. Publish release

## Post-Release Tasks

- [ ] Announce release on GitHub Discussions
- [ ] Update documentation if needed
- [ ] Respond to any issues that arise
- [ ] Monitor PyPI download statistics

## Version Numbering

Follow Semantic Versioning (semver):
- `MAJOR.MINOR.PATCH` (e.g., `1.2.3`)
- **MAJOR**: Breaking changes
- **MINOR**: New features, backwards compatible
- **PATCH**: Bug fixes, backwards compatible

### Pre-release Versions
- Alpha: `0.1.0a1`, `0.1.0a2`
- Beta: `0.1.0b1`, `0.1.0b2`
- Release Candidate: `0.1.0rc1`, `0.1.0rc2`

## Troubleshooting

### Error: "File already exists"
You cannot overwrite a published version. You must:
1. Delete files from TestPyPI (if testing)
2. Increment version number
3. Rebuild and re-upload

### Error: "Invalid or non-existent authentication"
- Ensure you're using `__token__` as username
- Verify API token is correct
- Check token hasn't expired or been revoked

### Error: "403 Forbidden"
- Project name may be taken
- You may not have permissions
- 2FA may be required

### Warning: "long_description_content_type missing"
Ensure `long_description_content_type="text/markdown"` in `setup.py`.

### Package Missing Files
Check `MANIFEST.in` includes all necessary files.

## Updating an Existing Release

### Patch Release (e.g., 0.1.0 → 0.1.1)
1. Make bug fixes
2. Update version numbers
3. Update CHANGELOG.md
4. Create git tag
5. Build and publish

### Minor Release (e.g., 0.1.0 → 0.2.0)
1. Add new features
2. Update version numbers
3. Update CHANGELOG.md
4. Update documentation
5. Create git tag
6. Build and publish

### Major Release (e.g., 0.1.0 → 1.0.0)
1. Finalize breaking changes
2. Update all documentation
3. Update migration guide
4. Update version numbers
5. Update CHANGELOG.md
6. Create git tag
7. Build and publish
8. Announce widely

## CI/CD Automation (Future Enhancement)

Consider automating releases with GitHub Actions:

```yaml
# .github/workflows/publish.yml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: "3.11"
    - name: Install dependencies
      run: |
        pip install build twine
    - name: Build package
      run: python -m build
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

## Security Best Practices

1. **Never commit API tokens** to git
2. **Use API tokens**, not passwords
3. **Enable 2FA** on PyPI account
4. **Use scoped tokens** (project-specific)
5. **Rotate tokens** periodically
6. **Use `.pypirc`** with restricted permissions (600)

## Resources

- PyPI: https://pypi.org/
- TestPyPI: https://test.pypi.org/
- Packaging Guide: https://packaging.python.org/
- Twine Documentation: https://twine.readthedocs.io/
- PEP 517 (Build): https://peps.python.org/pep-0517/
- PEP 621 (pyproject.toml): https://peps.python.org/pep-0621/

## Quick Reference

```bash
# Complete release workflow
VERSION="0.1.0"

# 1. Update version numbers
vim setup.py pyproject.toml emc2305/__init__.py CHANGELOG.md

# 2. Run tests
pytest tests/ -v
black --check emc2305/ tests/
ruff check emc2305/

# 3. Commit and tag
git add -A
git commit -m "chore: prepare release v${VERSION}"
git tag -a "v${VERSION}" -m "Release ${VERSION}"
git push origin main --tags

# 4. Build
rm -rf build/ dist/ *.egg-info
python -m build
twine check dist/*

# 5. Test on TestPyPI
twine upload --repository testpypi dist/*

# 6. Verify TestPyPI installation
python3 -m venv test-env && source test-env/bin/activate
pip install --index-url https://test.pypi.org/simple/     --extra-index-url https://pypi.org/simple/ microchip-emc2305

# 7. Publish to PyPI
twine upload dist/*

# 8. Verify PyPI installation
deactivate
python3 -m venv prod-env && source prod-env/bin/activate
pip install microchip-emc2305
python3 -c "import emc2305; print(emc2305.__version__)"
```

---

**Ready to publish?** Follow the checklist above and publish with confidence!
