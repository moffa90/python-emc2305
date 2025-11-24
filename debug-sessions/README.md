# Debug Sessions

This directory contains debugging documentation, test scripts, and hardware validation data from specific debugging sessions. These files are not part of the core library and are kept for reference only.

**This directory is git-ignored** - these files are specific to hardware debugging and not relevant to the library itself.

## Session Directory Structure

Each debugging session is stored in a dated subdirectory:

```
debug-sessions/
├── YYYY-MM-DD-issue-description/
│   ├── *.md                    # Debugging documentation
│   ├── *.pdf                   # PDF exports of documentation
│   ├── test-scripts/           # Test scripts used during debugging
│   ├── archived-test-scripts/  # Older test iterations
│   └── oscilloscope-captures/  # Hardware measurement data
```

## Available Sessions

### 2025-11-20-emc2305-voltage-mismatch

**Issue:** EMC2305 fan controller not spinning Wakefield DC0351005W2B-BTO fans

**Root Cause:** Voltage level mismatch - EMC2305 outputs 3.3V PWM, fan requires 5V PWM

**Solution:** Hardware level shifter circuit required (see SOLUTION.md in session folder)

**Key Discoveries:**
- GLBL_EN bit (register 0x20, bit 1) must be enabled for PWM outputs to work
- UPDATE_TIME must be 200ms (500ms breaks PWM control)
- Drive Fail Band register addresses corrected (0x3A/0x3B, not 0x3B/0x3C)
- PWM polarity configuration is fan-specific

**Files:**
- `FINAL_DIAGNOSIS.md` / `FINAL_DIAGNOSIS.pdf` - Complete root cause analysis
- `SOLUTION.md` / `SOLUTION.pdf` - Level shifter circuit designs with BOM
- `TROUBLESHOOTING_SESSION.md` - Complete debugging timeline
- `HOW_TO_CONTINUE.md` - Guide for resuming work
- `QUICK_REFERENCE.md` - Quick lookup reference
- `README_SESSION_COMPLETE.md` - Final session summary
- `test-scripts/` - Essential test scripts (6 scripts)
- `archived-test-scripts/` - Older test iterations (22 scripts)
- `oscilloscope-captures/` - Oscilloscope measurements (3 images)

**Fixes Applied to Library:**
1. CONFIG_GLBL_EN constant added and enabled in initialization
2. UPDATE_TIME default changed from 500ms to 200ms
3. Drive Fail Band register addresses corrected
4. Minimum drive percent changed from 20% to 0%

---

### 2025-11-24-register-readback-investigation

**Issue:** PWM register (0x30) readback values sometimes differ from written values

**Root Cause:** Hardware quantization anomaly at specific duty cycles (25% reads as 30%), but physical PWM output is correct

**Solution:** Documented as known hardware behavior. Optional verification method added to driver.

**Key Discoveries:**
- EMC2305 register readback is 80% accurate (4/5 test points: 0%, 50%, 75%, 100%)
- 25% PWM (0x40) reads back as 0x4C (~30%) due to internal quantization
- Physical PWM signal is correct (verified with oscilloscope)
- No functional impact - fan operates correctly
- Two configuration issues corrected: PWM output mode and polarity

**Files:**
- `README.md` - Session summary with test results
- `debug_pwm_readback.sh` - Comprehensive diagnostic script
- `oscilloscope_pwm_test.py` - PWM signal generation for measurement
- `test_open_drain_5v.py` - Open-drain configuration validation
- `test_remote_emc2305.py` - Remote I2C communication testing

**Enhancements Applied to Library:**
1. Added `set_pwm_duty_cycle_verified()` method with configurable tolerance
2. Comprehensive documentation in `docs/development/register-readback-findings.md`
3. Updated CLAUDE.md with register readback quantization section
4. Verified all critical configurations (GLBL_EN, open-drain, polarity)

---

**Last Updated:** 2025-11-24
