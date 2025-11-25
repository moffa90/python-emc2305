# Copyright (c) 2025 Contributors to the microchip-emc2305 project
# SPDX-License-Identifier: MIT

"""
Unit Tests for EMC2305 Driver

Tests driver logic without requiring actual hardware using mock I2C bus.
"""

import pytest
from mock_i2c import MockI2CBus

from emc2305.driver import constants as const
from emc2305.driver.emc2305 import (
    EMC2305,
    ControlMode,
    EMC2305DeviceNotFoundError,
    EMC2305ValidationError,
    FanConfig,
    FanStatus,
)


@pytest.fixture
def mock_bus():
    """Create mock I2C bus for testing."""
    return MockI2CBus(device_address=0x4D)


@pytest.fixture
def emc2305(mock_bus):
    """Create EMC2305 instance with mock bus."""
    return EMC2305(i2c_bus=mock_bus, device_address=0x4D)


# =============================================================================
# Device Detection Tests
# =============================================================================


def test_device_detection_success(mock_bus):
    """Test successful device detection."""
    controller = EMC2305(i2c_bus=mock_bus, device_address=0x4D)
    assert controller.product_id == 0x34
    assert controller.manufacturer_id == 0x5D


def test_device_detection_wrong_address(mock_bus):
    """Test device detection fails with wrong address."""
    with pytest.raises(EMC2305DeviceNotFoundError):
        EMC2305(i2c_bus=mock_bus, device_address=0x2F)  # Wrong address


def test_device_detection_wrong_product_id(mock_bus):
    """Test device detection fails with wrong product ID."""
    mock_bus.set_register(0xFD, 0xFF)  # Wrong product ID
    with pytest.raises(EMC2305DeviceNotFoundError):
        EMC2305(i2c_bus=mock_bus, device_address=0x4D)


# =============================================================================
# Initialization Tests
# =============================================================================


def test_initialization_enables_glbl_en(emc2305, mock_bus):
    """Test that initialization enables GLBL_EN bit."""
    config = mock_bus.get_register(const.REG_CONFIGURATION)
    assert config & const.CONFIG_GLBL_EN, "GLBL_EN bit must be enabled"


def test_initialization_disables_smbus_timeout(emc2305, mock_bus):
    """Test that initialization disables SMBus timeout."""
    config = mock_bus.get_register(const.REG_CONFIGURATION)
    assert config & const.CONFIG_DIS_TO, "SMBus timeout should be disabled"


def test_initialization_sets_pwm_polarity(emc2305, mock_bus):
    """Test that initialization sets PWM polarity."""
    polarity = mock_bus.get_register(const.REG_PWM_POLARITY_CONFIG)
    assert polarity == const.DEFAULT_PWM_POLARITY


def test_initialization_sets_pwm_output_mode(emc2305, mock_bus):
    """Test that initialization sets PWM output mode."""
    output_mode = mock_bus.get_register(const.REG_PWM_OUTPUT_CONFIG)
    assert output_mode == const.DEFAULT_PWM_OUTPUT_CONFIG


# =============================================================================
# PWM Control Tests
# =============================================================================


def test_set_pwm_duty_cycle_valid(emc2305, mock_bus):
    """Test setting PWM duty cycle with valid values."""
    test_values = [0.0, 25.0, 50.0, 75.0, 100.0]
    for percent in test_values:
        emc2305.set_pwm_duty_cycle(1, percent)
        pwm_reg = mock_bus.get_register(const.REG_FAN1_SETTING)
        expected_pwm = int((percent / 100.0) * 255)
        assert pwm_reg == expected_pwm, f"Failed for {percent}%"


def test_set_pwm_duty_cycle_invalid_channel(emc2305):
    """Test setting PWM with invalid channel."""
    with pytest.raises(EMC2305ValidationError):
        emc2305.set_pwm_duty_cycle(0, 50.0)  # Channel 0 invalid

    with pytest.raises(EMC2305ValidationError):
        emc2305.set_pwm_duty_cycle(6, 50.0)  # Channel 6 invalid


def test_set_pwm_duty_cycle_invalid_percent(emc2305):
    """Test setting PWM with invalid percentage."""
    with pytest.raises(EMC2305ValidationError):
        emc2305.set_pwm_duty_cycle(1, -1.0)  # Negative

    with pytest.raises(EMC2305ValidationError):
        emc2305.set_pwm_duty_cycle(1, 101.0)  # Over 100%


def test_get_pwm_duty_cycle(emc2305, mock_bus):
    """Test reading PWM duty cycle."""
    # Set known value
    mock_bus.set_register(const.REG_FAN1_SETTING, 128)  # 50%

    percent = emc2305.get_pwm_duty_cycle(1)
    assert 49.0 <= percent <= 51.0, f"Expected ~50%, got {percent}%"


def test_pwm_all_channels(emc2305, mock_bus):
    """Test PWM control works for all 5 channels."""
    for channel in range(1, 6):
        emc2305.set_pwm_duty_cycle(channel, 75.0)
        reg_offset = (channel - 1) * const.FAN_CHANNEL_OFFSET
        pwm_reg = mock_bus.get_register(const.REG_FAN1_SETTING + reg_offset)
        assert pwm_reg == 191  # 75% of 255


# =============================================================================
# RPM Control Tests
# =============================================================================


def test_set_target_rpm_valid(emc2305, mock_bus):
    """Test setting target RPM with valid values."""
    emc2305.set_target_rpm(1, 3000)

    # Verify TACH target registers were written
    tach_high = mock_bus.get_register(const.REG_FAN1_TACH_TARGET_HIGH)
    tach_low = mock_bus.get_register(const.REG_FAN1_TACH_TARGET_LOW)

    assert tach_high is not None
    assert tach_low is not None


def test_set_target_rpm_invalid_range(emc2305):
    """Test setting RPM outside valid range."""
    with pytest.raises(EMC2305ValidationError):
        emc2305.set_target_rpm(1, 400)  # Below minimum

    with pytest.raises(EMC2305ValidationError):
        emc2305.set_target_rpm(1, 17000)  # Above maximum


def test_get_current_rpm(emc2305, mock_bus):
    """Test reading current RPM."""
    # Mock TACH reading for ~3000 RPM
    # Formula: RPM = ((edges-1) * TACH_FREQ * 60) / (TACH_COUNT * poles)
    # With internal clock 32768 Hz, 2-pole fan (edges=5):
    #   count = ((5-1) * 32768 * 60) / (3000 * 2) = 1311
    # Register format: raw = (high << 8) | low, count = raw >> 3
    # So raw = 1311 << 3 = 10488 = 0x28F8
    # high = 0x28, low = 0xF8
    mock_bus.set_register(const.REG_FAN1_TACH_READING_HIGH, 0x28)
    mock_bus.set_register(const.REG_FAN1_TACH_READING_LOW, 0xF8)

    rpm = emc2305.get_current_rpm(1)
    assert 2800 <= rpm <= 3200, f"Expected ~3000 RPM, got {rpm}"


# =============================================================================
# Control Mode Tests
# =============================================================================


def test_set_control_mode_pwm(emc2305, mock_bus):
    """Test switching to PWM control mode."""
    # max_step must be 0-63 per hardware specification
    config = FanConfig(control_mode=ControlMode.PWM, max_step=31)
    emc2305.configure_fan(1, config)

    # Verify EN_ALGO bit is cleared
    config1 = mock_bus.get_register(const.REG_FAN1_CONFIG1)
    assert (config1 & const.FAN_CONFIG1_EN_ALGO) == 0


def test_set_control_mode_fsc(emc2305, mock_bus):
    """Test switching to FSC control mode."""
    # max_step must be 0-63 per hardware specification
    config = FanConfig(control_mode=ControlMode.FSC, max_step=31)
    emc2305.configure_fan(1, config)

    # Verify EN_ALGO bit is set
    config1 = mock_bus.get_register(const.REG_FAN1_CONFIG1)
    assert (config1 & const.FAN_CONFIG1_EN_ALGO) != 0


# =============================================================================
# Status Monitoring Tests
# =============================================================================


def test_get_fan_status_ok(emc2305, mock_bus):
    """Test getting fan status when all is OK."""
    mock_bus.clear_faults()
    status = emc2305.get_fan_status(1)
    assert status == FanStatus.OK


def test_get_fan_status_stalled(emc2305, mock_bus):
    """Test detecting stalled fan."""
    mock_bus.simulate_fault("stall", channel=1)
    status = emc2305.get_fan_status(1)
    assert status == FanStatus.STALLED


def test_get_fan_status_spin_failure(emc2305, mock_bus):
    """Test detecting spin-up failure."""
    mock_bus.simulate_fault("spin", channel=1)
    status = emc2305.get_fan_status(1)
    assert status == FanStatus.SPIN_FAILURE


def test_get_fan_status_drive_failure(emc2305, mock_bus):
    """Test detecting drive failure (aging fan)."""
    mock_bus.simulate_fault("drive_fail", channel=1)
    status = emc2305.get_fan_status(1)
    assert status == FanStatus.DRIVE_FAILURE


def test_get_all_fan_states(emc2305, mock_bus):
    """Test getting state for all fans."""
    mock_bus.simulate_fault("stall", channel=2)
    mock_bus.simulate_fault("spin", channel=3)

    states = emc2305.get_all_fan_states()

    assert states[1].status == FanStatus.OK
    assert states[2].status == FanStatus.STALLED
    assert states[3].status == FanStatus.SPIN_FAILURE
    assert states[4].status == FanStatus.OK
    assert states[5].status == FanStatus.OK


# =============================================================================
# Configuration Tests
# =============================================================================


def test_configure_fan_update_time(emc2305, mock_bus):
    """Test configuring fan update time."""
    # max_step must be 0-63 per hardware specification
    config = FanConfig(update_time_ms=200, max_step=31)
    emc2305.configure_fan(1, config)

    config1 = mock_bus.get_register(const.REG_FAN1_CONFIG1)
    # 200ms = 0x20 in bits 7-5
    assert (config1 & const.FAN_CONFIG1_UPDATE_MASK) == const.FAN_CONFIG1_UPDATE_200MS


def test_configure_fan_tach_edges(emc2305, mock_bus):
    """Test configuring tachometer edges."""
    # max_step must be 0-63 per hardware specification
    config = FanConfig(edges=5, max_step=31)  # 2-pole fan
    emc2305.configure_fan(1, config)

    config1 = mock_bus.get_register(const.REG_FAN1_CONFIG1)
    # 5 edges = 0x08 in bits 4-3
    assert (config1 & const.FAN_CONFIG1_EDGES_MASK) == const.FAN_CONFIG1_EDGES_5


def test_configure_fan_minimum_drive(emc2305, mock_bus):
    """Test configuring minimum drive level."""
    # max_step must be 0-63 per hardware specification
    config = FanConfig(min_drive_percent=20, max_step=31)
    emc2305.configure_fan(1, config)

    min_drive = mock_bus.get_register(const.REG_FAN1_MINIMUM_DRIVE)
    expected = int((20 / 100.0) * 255)
    assert min_drive == expected


# =============================================================================
# Conversion Method Tests
# =============================================================================


def test_percent_to_pwm_conversion(emc2305):
    """Test percent to PWM value conversion."""
    assert emc2305._percent_to_pwm(0.0) == 0
    assert emc2305._percent_to_pwm(50.0) == 127
    assert emc2305._percent_to_pwm(100.0) == 255


def test_pwm_to_percent_conversion(emc2305):
    """Test PWM value to percent conversion."""
    assert emc2305._pwm_to_percent(0) == 0.0
    assert 49.0 <= emc2305._pwm_to_percent(127) <= 51.0
    assert emc2305._pwm_to_percent(255) == 100.0


def test_rpm_to_tach_count_conversion(emc2305):
    """Test RPM to tachometer count conversion."""
    # Formula: count = ((edges-1) * TACH_FREQ * 60) / (RPM * poles)
    # With internal clock 32768 Hz, 2-pole fan (edges=5):
    #   count = ((5-1) * 32768 * 60) / (3000 * 2) = 1310.72 ≈ 1311
    count = emc2305._rpm_to_tach_count(3000, edges=5)
    assert 1300 <= count <= 1320, f"Expected ~1311, got {count}"


def test_tach_count_to_rpm_conversion(emc2305):
    """Test tachometer count to RPM conversion."""
    # Count of 1311 with 5 edges (2-pole fan) should give ~3000 RPM
    # Formula: RPM = ((edges-1) * TACH_FREQ * 60) / (TACH_COUNT * poles)
    # RPM = ((5-1) * 32768 * 60) / (1311 * 2) = 3000.12
    rpm = emc2305._tach_count_to_rpm(1311, edges=5)
    assert 2900 <= rpm <= 3100, f"Expected ~3000 RPM, got {rpm}"


# =============================================================================
# Validation Tests
# =============================================================================


def test_validate_channel(emc2305):
    """Test channel validation."""
    # Valid channels should not raise
    for channel in range(1, 6):
        emc2305._validate_channel(channel)  # Should not raise

    # Invalid channels should raise
    with pytest.raises(EMC2305ValidationError):
        emc2305._validate_channel(0)

    with pytest.raises(EMC2305ValidationError):
        emc2305._validate_channel(6)


def test_validate_percent(emc2305):
    """Test percentage validation."""
    # Valid percentages
    emc2305._validate_percent(0.0)
    emc2305._validate_percent(50.0)
    emc2305._validate_percent(100.0)

    # Invalid percentages
    with pytest.raises(EMC2305ValidationError):
        emc2305._validate_percent(-1.0)

    with pytest.raises(EMC2305ValidationError):
        emc2305._validate_percent(101.0)


def test_validate_rpm(emc2305):
    """Test RPM validation."""
    # Valid RPMs
    emc2305._validate_rpm(500, const.MIN_RPM, const.MAX_RPM)
    emc2305._validate_rpm(3000, const.MIN_RPM, const.MAX_RPM)
    emc2305._validate_rpm(16000, const.MIN_RPM, const.MAX_RPM)

    # Invalid RPMs
    with pytest.raises(EMC2305ValidationError):
        emc2305._validate_rpm(400, const.MIN_RPM, const.MAX_RPM)

    with pytest.raises(EMC2305ValidationError):
        emc2305._validate_rpm(17000, const.MIN_RPM, const.MAX_RPM)


# =============================================================================
# PWM Verification Tests
# =============================================================================


def test_set_pwm_verified_success(emc2305, mock_bus):
    """Test verified PWM setting succeeds with matching readback."""
    success, actual = emc2305.set_pwm_duty_cycle_verified(1, 50.0, tolerance=5.0)
    assert success is True
    assert 45.0 <= actual <= 55.0


def test_set_pwm_verified_with_tolerance(emc2305, mock_bus):
    """Test verified PWM accepts values within tolerance."""
    # Mock the quantization anomaly (25% → 30%)
    # 25% = 64/255, 30% = 76/255

    # After write, simulate readback as 76 (30%)
    def mock_write(addr, reg, val):
        mock_bus._registers[reg] = 76 if val == 64 else val

    original_write = mock_bus.write_byte
    mock_bus.write_byte = mock_write

    # Use tolerance of 10% to account for the 5% quantization difference
    success, actual = emc2305.set_pwm_duty_cycle_verified(1, 25.0, tolerance=10.0)

    mock_bus.write_byte = original_write

    # Should succeed because 30% is within 10% tolerance of 25%
    assert success is True
    assert 20.0 <= actual <= 35.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
