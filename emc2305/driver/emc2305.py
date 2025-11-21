# Copyright (c) 2025 Contributors to the microchip-emc2305 project
# SPDX-License-Identifier: MIT

"""
EMC2305 Fan Controller Driver

Driver for the SMSC/Microchip EMC2305 5-Channel PWM Fan Controller.

Features:
- 5 independent PWM fan channels
- Direct PWM control mode (0-100% duty cycle)
- FSC (Fan Speed Control) closed-loop RPM control with PID
- RPM monitoring via tachometer
- Stall detection and spin-up failure detection
- Aging fan detection (drive fail)
- Programmable PWM frequency
- Watchdog timer support
- ALERT# pin for fault notification
"""

import logging
import time
import threading
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass

from emc2305.driver.i2c import I2CBus, I2CError
from emc2305.driver import constants as const

logger = logging.getLogger(__name__)


class ControlMode(Enum):
    """Fan control mode."""
    PWM = "pwm"  # Direct PWM control (0-100%)
    FSC = "fsc"  # Fan Speed Control (closed-loop RPM control)


class FanStatus(Enum):
    """Fan operational status."""
    OK = "ok"
    STALLED = "stalled"
    SPIN_FAILURE = "spin_failure"
    DRIVE_FAILURE = "drive_failure"
    UNKNOWN = "unknown"


@dataclass
class FanConfig:
    """Configuration for a single fan channel."""
    enabled: bool = True
    control_mode: ControlMode = ControlMode.PWM
    min_rpm: int = const.MIN_RPM
    max_rpm: int = const.MAX_RPM
    min_drive_percent: int = 0  # Changed from 20 to 0 for unrestricted PWM control
    max_step: int = const.DEFAULT_MAX_STEP
    update_time_ms: int = 200  # CRITICAL: 500ms breaks PWM control! Must use 200ms (factory default)
    edges: int = 5  # Tachometer edges (3/5/7/9 for 1/2/3/4-pole fans)
    spin_up_level_percent: int = 50
    spin_up_time_ms: int = 500
    pid_gain_p: int = 2  # Proportional gain multiplier (1/2/4/8)
    pid_gain_i: int = 1  # Integral gain multiplier (0/1/2/4/8/16/32)
    pid_gain_d: int = 1  # Derivative gain multiplier (0/1/2/4/8/16/32)

    # PWM Frequency Control
    pwm_divide: int = const.DEFAULT_PWM_DIVIDE  # PWM frequency divider (1, 2, 4, 8, 16, 32)

    # CONFIG2 Register Settings (Advanced)
    error_range_rpm: int = 0  # Error window: 0, 50, 100, or 200 RPM
    derivative_mode: int = 0  # Derivative option: 0-7 (see datasheet Section 3.3.4)
    glitch_filter_enabled: bool = True  # Enable tachometer glitch filtering

    # Drive Fail Band Settings (Aging Fan Detection)
    drive_fail_band_rpm: int = 0  # RPM band for aging fan detection (0 = disabled)
    valid_tach_count: int = const.DEFAULT_VALID_TACH_COUNT  # Minimum valid tach count for stall detection


@dataclass
class FanState:
    """Current state of a single fan channel."""
    channel: int
    enabled: bool
    control_mode: ControlMode
    pwm_percent: float
    target_rpm: int
    current_rpm: int
    status: FanStatus


@dataclass
class ProductFeatures:
    """EMC2305 product features and capabilities."""
    fan_channels: int  # Number of fan channels (typically 5 for EMC2305)
    rpm_control_supported: bool  # RPM-based fan speed control support
    product_id: int  # Product ID (0x34 for EMC2305)
    manufacturer_id: int  # Manufacturer ID (0x5D for SMSC)
    revision: int  # Chip revision


class EMC2305Error(Exception):
    """Base exception for EMC2305 driver errors."""
    pass


class EMC2305DeviceNotFoundError(EMC2305Error):
    """Raised when EMC2305 device is not detected on I2C bus."""
    pass


class EMC2305ConfigurationError(EMC2305Error):
    """Raised when configuration is invalid or conflicts."""
    pass


class EMC2305ConfigurationLockedError(EMC2305Error):
    """Raised when attempting to modify locked configuration registers."""
    pass


class EMC2305CommunicationError(EMC2305Error):
    """Raised when I2C communication fails."""
    pass


class EMC2305ValidationError(EMC2305Error):
    """Raised when input validation fails."""
    pass


class EMC2305:
    """
    Driver for EMC2305 5-Channel PWM Fan Controller.

    Args:
        i2c_bus: I2CBus instance for communication
        device_address: I2C device address (default: 0x61)
        use_external_clock: Use external 32.768kHz clock (default: False)
        enable_watchdog: Enable 4-second watchdog timer (default: False)
        pwm_frequency: PWM base frequency in Hz (default: 26000)

    Example:
        >>> bus = I2CBus(bus_number=0)
        >>> fan_controller = EMC2305(bus, device_address=0x61)
        >>> fan_controller.set_pwm_duty_cycle(1, 50)  # Set fan 1 to 50%
        >>> rpm = fan_controller.get_current_rpm(1)
        >>> print(f"Fan 1 RPM: {rpm}")
    """

    def __init__(
        self,
        i2c_bus: I2CBus,
        device_address: int = const.DEFAULT_DEVICE_ADDRESS,
        use_external_clock: bool = False,
        enable_watchdog: bool = False,
        pwm_frequency: int = 26000,
    ):
        self.i2c_bus = i2c_bus
        self.address = device_address
        self.use_external_clock = use_external_clock
        self.enable_watchdog = enable_watchdog
        self.pwm_frequency = pwm_frequency

        # Thread safety for concurrent access
        self._lock = threading.Lock()

        # Fan configurations and states
        self._fan_configs: Dict[int, FanConfig] = {}
        self._fan_states: Dict[int, FanState] = {}

        # Software lock status
        self._is_locked: bool = False

        # Initialize device
        self._detect_device()
        self._initialize()

        logger.info(
            f"EMC2305 initialized at address 0x{self.address:02X} "
            f"(Product ID: 0x{self.product_id:02X}, Revision: 0x{self.revision:02X})"
        )

    def _detect_device(self) -> None:
        """
        Detect and validate EMC2305 device.

        Raises:
            EMC2305DeviceNotFoundError: If device is not found or invalid
        """
        try:
            # Read product ID
            product_id = self.i2c_bus.read_byte(self.address, const.REG_PRODUCT_ID)
            if product_id != const.PRODUCT_ID:
                raise EMC2305DeviceNotFoundError(
                    f"Invalid Product ID: expected 0x{const.PRODUCT_ID:02X}, "
                    f"got 0x{product_id:02X}"
                )

            # Read manufacturer ID
            mfg_id = self.i2c_bus.read_byte(self.address, const.REG_MANUFACTURER_ID)
            if mfg_id != const.MANUFACTURER_ID:
                raise EMC2305DeviceNotFoundError(
                    f"Invalid Manufacturer ID: expected 0x{const.MANUFACTURER_ID:02X}, "
                    f"got 0x{mfg_id:02X}"
                )

            # Read revision
            self.product_id = product_id
            self.manufacturer_id = mfg_id
            self.revision = self.i2c_bus.read_byte(self.address, const.REG_REVISION)

            logger.info(
                f"EMC2305 detected: Product=0x{product_id:02X}, "
                f"Manufacturer=0x{mfg_id:02X}, Revision=0x{self.revision:02X}"
            )

        except I2CError as e:
            raise EMC2305DeviceNotFoundError(
                f"Failed to detect EMC2305 at address 0x{self.address:02X}: {e}"
            )

    def _initialize(self) -> None:
        """Initialize EMC2305 with default configuration."""
        try:
            # Build configuration register value
            config = 0x00

            # Disable SMBus timeout for full I2C compliance
            config |= const.CONFIG_DIS_TO

            # CRITICAL: Enable global PWM output (GLBL_EN bit)
            # Without this bit enabled, ALL PWM outputs are disabled regardless of individual fan settings
            config |= const.CONFIG_GLBL_EN
            logger.info("Global PWM output enabled (GLBL_EN)")

            # Enable watchdog if requested
            if self.enable_watchdog:
                config |= const.CONFIG_WD_EN
                logger.info("Watchdog timer enabled (4 second timeout)")

            # Configure clock source
            if self.use_external_clock:
                config |= const.CONFIG_USE_EXT_CLK
                logger.info("Using external 32.768 kHz clock")
            else:
                logger.info("Using internal oscillator")

            # Write configuration
            self.i2c_bus.write_byte(self.address, const.REG_CONFIGURATION, config)

            # Configure PWM frequency for all fans
            self._configure_pwm_frequency()

            # Set default PWM polarity (normal) and output type (open-drain)
            self.i2c_bus.write_byte(self.address, const.REG_PWM_POLARITY_CONFIG, const.DEFAULT_PWM_POLARITY)
            self.i2c_bus.write_byte(self.address, const.REG_PWM_OUTPUT_CONFIG, const.DEFAULT_PWM_OUTPUT_CONFIG)

            # Initialize all fan channels with default configuration
            for channel in range(1, const.NUM_FAN_CHANNELS + 1):
                default_config = FanConfig()
                self._fan_configs[channel] = default_config
                self._configure_fan_registers(channel, default_config)

            # Enable interrupts for all fans (for ALERT# pin)
            self.i2c_bus.write_byte(
                self.address,
                const.REG_FAN_INTERRUPT_ENABLE,
                const.FAN_INTERRUPT_ENABLE_ALL_FANS  # Enable fans 1-5 (bits 0-4)
            )

            # Clear any existing fault status
            self._clear_fault_status()

            time.sleep(const.INIT_DELAY_MS / 1000.0)

        except I2CError as e:
            raise EMC2305Error(f"Failed to initialize EMC2305: {e}")

    def _configure_pwm_frequency(self) -> None:
        """Configure PWM base frequency for all fans."""
        # Map requested frequency to closest supported base frequency
        if self.pwm_frequency >= const.PWM_FREQ_26000HZ_THRESHOLD:
            freq_code = const.PWM_FREQ_26000HZ
            actual_freq = 26000
        elif self.pwm_frequency >= const.PWM_FREQ_19531HZ_THRESHOLD:
            freq_code = const.PWM_FREQ_19531HZ
            actual_freq = 19531
        elif self.pwm_frequency >= const.PWM_FREQ_4882HZ_THRESHOLD:
            freq_code = const.PWM_FREQ_4882HZ
            actual_freq = 4882
        else:
            freq_code = const.PWM_FREQ_2441HZ
            actual_freq = 2441

        # Set base frequency for fans 1-3
        self.i2c_bus.write_byte(self.address, const.REG_PWM_BASE_FREQ_1, freq_code)

        # Set base frequency for fans 4-5
        self.i2c_bus.write_byte(self.address, const.REG_PWM_BASE_FREQ_2, freq_code)

        logger.info(
            f"PWM base frequency set to {actual_freq} Hz "
            f"(requested: {self.pwm_frequency} Hz)"
        )

    def _configure_fan_registers(self, channel: int, config: FanConfig) -> None:
        """
        Configure all registers for a specific fan channel.

        Args:
            channel: Fan channel number (1-5)
            config: Fan configuration
        """
        self._validate_channel(channel)

        # Calculate register base address for this channel
        base = const.REG_FAN1_SETTING + (channel - 1) * const.FAN_CHANNEL_OFFSET

        # Set PWM divide for per-fan frequency control
        # Final PWM frequency = Base Frequency / pwm_divide
        pwm_divide = config.pwm_divide
        if pwm_divide < 1 or pwm_divide > 255:
            raise EMC2305ValidationError(
                f"PWM divide must be 1-255, got {pwm_divide}"
            )
        if pwm_divide not in const.VALID_PWM_DIVIDES:
            logger.warning(
                f"Fan {channel}: PWM divide {pwm_divide} is not a standard value. "
                f"Recommended values: {const.VALID_PWM_DIVIDES}"
            )

        self.i2c_bus.write_byte(
            self.address,
            base + (const.REG_FAN1_PWM_DIVIDE - const.REG_FAN1_SETTING),
            pwm_divide
        )
        logger.debug(f"Fan {channel} PWM divide set to {pwm_divide}")

        # Build CONFIG1 register
        config1 = 0x00

        # Set update time
        update_map = {
            100: const.FAN_CONFIG1_UPDATE_100MS,
            200: const.FAN_CONFIG1_UPDATE_200MS,
            300: const.FAN_CONFIG1_UPDATE_300MS,
            400: const.FAN_CONFIG1_UPDATE_400MS,
            500: const.FAN_CONFIG1_UPDATE_500MS,
            800: const.FAN_CONFIG1_UPDATE_800MS,
            1200: const.FAN_CONFIG1_UPDATE_1200MS,
            1600: const.FAN_CONFIG1_UPDATE_1600MS,
        }
        config1 |= update_map.get(config.update_time_ms, const.DEFAULT_UPDATE_TIME)

        # Set tachometer edges
        edges_map = {
            3: const.FAN_CONFIG1_EDGES_3,
            5: const.FAN_CONFIG1_EDGES_5,
            7: const.FAN_CONFIG1_EDGES_7,
            9: const.FAN_CONFIG1_EDGES_9,
        }
        config1 |= edges_map.get(config.edges, const.DEFAULT_EDGES)

        # Enable FSC algorithm if in FSC mode
        if config.control_mode == ControlMode.FSC:
            config1 |= const.FAN_CONFIG1_EN_ALGO
            config1 |= const.FAN_CONFIG1_EN_RRC  # Enable ramp rate control

        # Write CONFIG1
        self.i2c_bus.write_byte(
            self.address,
            base + (const.REG_FAN1_CONFIG1 - const.REG_FAN1_SETTING),
            config1
        )

        # Build CONFIG2 register
        config2 = 0x00

        # Set error range
        error_range_map = {
            0: const.FAN_CONFIG2_ERR_RNG_0,
            50: const.FAN_CONFIG2_ERR_RNG_50,
            100: const.FAN_CONFIG2_ERR_RNG_100,
            200: const.FAN_CONFIG2_ERR_RNG_200,
        }
        config2 |= error_range_map.get(config.error_range_rpm, const.FAN_CONFIG2_ERR_RNG_0)

        # Set derivative option (0-7)
        derivative_options = [
            const.FAN_CONFIG2_DER_OPT_NONE,
            const.FAN_CONFIG2_DER_OPT_1,
            const.FAN_CONFIG2_DER_OPT_2,
            const.FAN_CONFIG2_DER_OPT_3,
            const.FAN_CONFIG2_DER_OPT_4,
            const.FAN_CONFIG2_DER_OPT_5,
            const.FAN_CONFIG2_DER_OPT_6,
            const.FAN_CONFIG2_DER_OPT_7,
        ]
        if 0 <= config.derivative_mode <= 7:
            config2 |= derivative_options[config.derivative_mode]

        # Set glitch filter
        if config.glitch_filter_enabled:
            config2 |= const.FAN_CONFIG2_GLITCH_EN

        # Set RPM range (500-16k for internal clock)
        if self.use_external_clock:
            config2 |= const.FAN_CONFIG2_RNG_1K_32K
        else:
            config2 |= const.FAN_CONFIG2_RNG_500_16K

        # Write CONFIG2
        self.i2c_bus.write_byte(
            self.address,
            base + (const.REG_FAN1_CONFIG2 - const.REG_FAN1_SETTING),
            config2
        )

        # Set PID gains
        gain = 0x00

        # Proportional gain
        p_map = {1: const.GAIN_P_1X, 2: const.GAIN_P_2X, 4: const.GAIN_P_4X, 8: const.GAIN_P_8X}
        gain |= p_map.get(config.pid_gain_p, const.GAIN_P_2X)

        # Integral gain
        i_map = {
            0: const.GAIN_I_0X, 1: const.GAIN_I_1X, 2: const.GAIN_I_2X,
            4: const.GAIN_I_4X, 8: const.GAIN_I_8X, 16: const.GAIN_I_16X, 32: const.GAIN_I_32X
        }
        gain |= i_map.get(config.pid_gain_i, const.GAIN_I_1X)

        # Derivative gain
        d_map = {
            0: const.GAIN_D_0X, 1: const.GAIN_D_1X, 2: const.GAIN_D_2X,
            4: const.GAIN_D_4X, 8: const.GAIN_D_8X, 16: const.GAIN_D_16X, 32: const.GAIN_D_32X
        }
        gain |= d_map.get(config.pid_gain_d, const.GAIN_D_1X)

        self.i2c_bus.write_byte(
            self.address,
            base + (const.REG_FAN1_GAIN - const.REG_FAN1_SETTING),
            gain
        )

        # Configure spin-up
        spin_level_map = {
            30: const.SPIN_UP_LEVEL_30_PERCENT,
            35: const.SPIN_UP_LEVEL_35_PERCENT,
            40: const.SPIN_UP_LEVEL_40_PERCENT,
            45: const.SPIN_UP_LEVEL_45_PERCENT,
            50: const.SPIN_UP_LEVEL_50_PERCENT,
            55: const.SPIN_UP_LEVEL_55_PERCENT,
            60: const.SPIN_UP_LEVEL_60_PERCENT,
            65: const.SPIN_UP_LEVEL_65_PERCENT,
        }
        # Find closest spin-up level
        closest_level = min(spin_level_map.keys(), key=lambda x: abs(x - config.spin_up_level_percent))
        spin_config = spin_level_map[closest_level]

        # Spin-up time in SPIN_UP_TIME_UNIT_MS units (0-SPIN_UP_TIME_MAX_VALUE)
        spin_time = min(const.SPIN_UP_TIME_MAX_VALUE, max(0, config.spin_up_time_ms // const.SPIN_UP_TIME_UNIT_MS))
        spin_config |= spin_time

        self.i2c_bus.write_byte(
            self.address,
            base + (const.REG_FAN1_SPIN_UP_CONFIG - const.REG_FAN1_SETTING),
            spin_config
        )

        # Set maximum step
        self.i2c_bus.write_byte(
            self.address,
            base + (const.REG_FAN1_MAX_STEP - const.REG_FAN1_SETTING),
            config.max_step
        )

        # Set minimum drive level
        min_drive_pwm = self._percent_to_pwm(config.min_drive_percent)
        self.i2c_bus.write_byte(
            self.address,
            base + (const.REG_FAN1_MINIMUM_DRIVE - const.REG_FAN1_SETTING),
            min_drive_pwm
        )

        # Set valid TACH count for stall detection
        valid_tach = config.valid_tach_count
        self.i2c_bus.write_byte(
            self.address,
            base + (const.REG_FAN1_VALID_TACH_COUNT - const.REG_FAN1_SETTING),
            (valid_tach >> const.VALID_TACH_HIGH_SHIFT) & const.BYTE_MASK  # MSB
        )
        self.i2c_bus.write_byte(
            self.address,
            base + (const.REG_FAN1_VALID_TACH_COUNT_LSB - const.REG_FAN1_SETTING),
            valid_tach & const.BYTE_MASK  # LSB
        )

        # Set Drive Fail Band for aging fan detection
        # Convert RPM band to tachometer count difference
        if config.drive_fail_band_rpm > 0:
            # Calculate tach count at (target - band) to get the count difference
            # This represents how much the tach count can deviate below target
            drive_fail_band_count = self._rpm_to_tach_count(config.drive_fail_band_rpm)

            # Drive Fail Band Low Byte (0x3B) - bits 7:3 of count
            drive_fail_low = (drive_fail_band_count >> const.DRIVE_FAIL_LOW_SHIFT) & const.BYTE_MASK
            self.i2c_bus.write_byte(
                self.address,
                base + (const.REG_FAN1_DRIVE_FAIL_BAND_LOW - const.REG_FAN1_SETTING),
                drive_fail_low
            )

            # Drive Fail Band High Byte (0x3C) - bits 12:8 of count
            drive_fail_high = (drive_fail_band_count >> const.DRIVE_FAIL_HIGH_SHIFT) & const.DRIVE_FAIL_HIGH_MASK
            self.i2c_bus.write_byte(
                self.address,
                base + (const.REG_FAN1_DRIVE_FAIL_BAND_HIGH - const.REG_FAN1_SETTING),
                drive_fail_high
            )

            logger.debug(
                f"Fan {channel} Drive Fail Band configured: {config.drive_fail_band_rpm} RPM "
                f"(count={drive_fail_band_count}, low=0x{drive_fail_low:02X}, high=0x{drive_fail_high:02X})"
            )
        else:
            # Disable Drive Fail Band by writing 0
            self.i2c_bus.write_byte(
                self.address,
                base + (const.REG_FAN1_DRIVE_FAIL_BAND_LOW - const.REG_FAN1_SETTING),
                0x00
            )
            self.i2c_bus.write_byte(
                self.address,
                base + (const.REG_FAN1_DRIVE_FAIL_BAND_HIGH - const.REG_FAN1_SETTING),
                0x00
            )

        logger.debug(
            f"Fan {channel} configured: mode={config.control_mode.value}, "
            f"min_drive={config.min_drive_percent}%, spin_up={closest_level}%/{config.spin_up_time_ms}ms"
        )

    def _read_all_status_registers(self) -> tuple[int, int, int, int]:
        """
        Read all status registers in one optimized block read.

        Returns:
            Tuple of (fan_status, stall_status, spin_status, drive_fail_status)
        """
        # Read 4 consecutive status registers (0x24-0x27) in one I2C transaction
        status_block = self.i2c_bus.read_block(self.address, const.REG_FAN_STATUS, 4)
        return (status_block[0], status_block[1], status_block[2], status_block[3])

    def _clear_fault_status(self) -> None:
        """Clear all fault status registers."""
        # Reading status registers clears them (optimized with block read)
        self._read_all_status_registers()

    def _validate_channel(self, channel: int) -> None:
        """Validate fan channel number."""
        if not isinstance(channel, int):
            raise EMC2305ValidationError(
                f"Channel must be an integer, got {type(channel).__name__}"
            )
        if not 1 <= channel <= const.NUM_FAN_CHANNELS:
            raise EMC2305ValidationError(
                f"Invalid fan channel {channel}. Must be 1-{const.NUM_FAN_CHANNELS}"
            )

    def _validate_percent(self, percent: float) -> None:
        """Validate percentage value."""
        if not isinstance(percent, (int, float)):
            raise EMC2305ValidationError(
                f"Percentage must be a number, got {type(percent).__name__}"
            )
        if not 0 <= percent <= 100:
            raise EMC2305ValidationError(f"Percentage must be 0-100, got {percent}")

    def _validate_rpm(self, rpm: int, min_rpm: int = const.MIN_RPM, max_rpm: int = const.MAX_RPM) -> None:
        """Validate RPM value."""
        if not isinstance(rpm, int):
            raise EMC2305ValidationError(
                f"RPM must be an integer, got {type(rpm).__name__}"
            )
        if rpm < 0:
            raise EMC2305ValidationError(
                f"RPM cannot be negative, got {rpm}"
            )
        if not min_rpm <= rpm <= max_rpm:
            raise EMC2305ValidationError(
                f"RPM must be {min_rpm}-{max_rpm}, got {rpm}"
            )

    def _validate_pid_gain(self, gain: int, valid_gains: list[int], gain_name: str) -> None:
        """Validate PID gain value."""
        if not isinstance(gain, int):
            raise EMC2305ValidationError(
                f"{gain_name} gain must be an integer, got {type(gain).__name__}"
            )
        if gain not in valid_gains:
            raise EMC2305ValidationError(
                f"{gain_name} gain must be one of {valid_gains}, got {gain}"
            )

    def _validate_fan_config(self, config: FanConfig) -> None:
        """Comprehensive validation of fan configuration."""
        # Validate RPM limits
        if config.min_rpm >= config.max_rpm:
            raise EMC2305ValidationError(
                f"min_rpm ({config.min_rpm}) must be less than max_rpm ({config.max_rpm})"
            )
        self._validate_rpm(config.min_rpm)
        self._validate_rpm(config.max_rpm)

        # Validate PWM limits
        if not 0 <= config.min_drive_percent <= 100:
            raise EMC2305ValidationError(
                f"min_drive_percent must be 0-100, got {config.min_drive_percent}"
            )

        # Validate max step
        if not 0 <= config.max_step <= 63:
            raise EMC2305ValidationError(
                f"max_step must be 0-63, got {config.max_step}"
            )

        # Validate update time
        valid_update_times = [100, 200, 300, 400, 500, 800, 1200, 1600]
        if config.update_time_ms not in valid_update_times:
            raise EMC2305ValidationError(
                f"update_time_ms must be one of {valid_update_times}, got {config.update_time_ms}"
            )

        # Validate tachometer edges
        valid_edges = [3, 5, 7, 9]
        if config.edges not in valid_edges:
            raise EMC2305ValidationError(
                f"edges must be one of {valid_edges} (for 1/2/3/4-pole fans), got {config.edges}"
            )

        # Validate spin-up parameters
        if not 0 <= config.spin_up_time_ms <= 1550:
            raise EMC2305ValidationError(
                f"spin_up_time_ms must be 0-1550, got {config.spin_up_time_ms}"
            )
        valid_spin_up_levels = [30, 35, 40, 45, 50, 55, 60, 65]
        if config.spin_up_level_percent not in valid_spin_up_levels:
            raise EMC2305ValidationError(
                f"spin_up_level_percent must be one of {valid_spin_up_levels}, got {config.spin_up_level_percent}"
            )

        # Validate PID gains
        valid_p_gains = [1, 2, 4, 8]
        valid_id_gains = [0, 1, 2, 4, 8, 16, 32]
        self._validate_pid_gain(config.pid_gain_p, valid_p_gains, "Proportional")
        self._validate_pid_gain(config.pid_gain_i, valid_id_gains, "Integral")
        self._validate_pid_gain(config.pid_gain_d, valid_id_gains, "Derivative")

        # Validate PWM divide
        if not 1 <= config.pwm_divide <= 255:
            raise EMC2305ValidationError(
                f"pwm_divide must be 1-255, got {config.pwm_divide}"
            )

        # Validate CONFIG2 parameters
        valid_error_ranges = [0, 50, 100, 200]
        if config.error_range_rpm not in valid_error_ranges:
            raise EMC2305ValidationError(
                f"error_range_rpm must be one of {valid_error_ranges}, got {config.error_range_rpm}"
            )

        if not 0 <= config.derivative_mode <= 7:
            raise EMC2305ValidationError(
                f"derivative_mode must be 0-7, got {config.derivative_mode}"
            )

        # Validate Drive Fail Band
        if config.drive_fail_band_rpm < 0:
            raise EMC2305ValidationError(
                f"drive_fail_band_rpm cannot be negative, got {config.drive_fail_band_rpm}"
            )

        if config.valid_tach_count < 0 or config.valid_tach_count > const.TACH_COUNT_MAX:
            raise EMC2305ValidationError(
                f"valid_tach_count must be 0-{const.TACH_COUNT_MAX}, got {config.valid_tach_count}"
            )

    def _percent_to_pwm(self, percent: float) -> int:
        """Convert percentage (0-100) to PWM value (0-255)."""
        return int(percent * const.MAX_PWM_VALUE / 100.0)

    def _pwm_to_percent(self, pwm: int) -> float:
        """Convert PWM value (0-255) to percentage (0-100)."""
        return (pwm / const.MAX_PWM_VALUE) * 100.0

    def _rpm_to_tach_count(self, rpm: int) -> int:
        """
        Convert RPM to tachometer count value.

        Formula: TACH_COUNT = (TACH_FREQ * 60) / (RPM * poles)

        Args:
            rpm: Target RPM value

        Returns:
            13-bit tachometer count value

        Raises:
            EMC2305ValidationError: If RPM is out of valid range
        """
        if rpm == 0:
            return const.TACH_COUNT_MAX

        # Validate RPM range based on clock source
        max_rpm = const.MAX_RPM_EXT_CLOCK if self.use_external_clock else const.MAX_RPM
        if not const.MIN_RPM <= rpm <= max_rpm:
            raise EMC2305ValidationError(
                f"RPM {rpm} out of range (must be {const.MIN_RPM}-{max_rpm})"
            )

        tach_freq = (
            const.EXTERNAL_CLOCK_FREQ_HZ
            if self.use_external_clock
            else const.INTERNAL_CLOCK_FREQ_HZ
        )

        # Assume 2-pole fan (5 edges) - this should come from config
        poles = 2
        tach_count = (tach_freq * 60) // (rpm * poles)

        return min(const.TACH_COUNT_MAX, max(0, tach_count))

    def _tach_count_to_rpm(self, tach_count: int, edges: int = 5) -> int:
        """
        Convert tachometer count value to RPM.

        Formula: RPM = (TACH_FREQ * 60) / (TACH_COUNT * poles)

        Args:
            tach_count: 13-bit tachometer count value
            edges: Tachometer edges per revolution (3, 5, 7, or 9)

        Returns:
            RPM value

        Raises:
            EMC2305ValidationError: If tach_count or edges are invalid
        """
        if tach_count == 0:
            return 0

        # Validate tachometer count
        if not 0 <= tach_count <= const.TACH_COUNT_MAX:
            raise EMC2305ValidationError(
                f"Tachometer count {tach_count} out of range (must be 0-{const.TACH_COUNT_MAX})"
            )

        # Validate edges (3, 5, 7, or 9 for 1-4 pole fans)
        if edges not in [3, 5, 7, 9]:
            raise EMC2305ValidationError(
                f"Invalid tachometer edges {edges} (must be 3, 5, 7, or 9)"
            )

        tach_freq = (
            const.EXTERNAL_CLOCK_FREQ_HZ
            if self.use_external_clock
            else const.INTERNAL_CLOCK_FREQ_HZ
        )

        # Calculate poles from edges: edges = poles * 2 + 1
        # So: poles = (edges - 1) / 2
        poles = (edges - 1) // 2
        if poles == 0:
            poles = 2  # Default to 2-pole

        rpm = (tach_freq * 60) // (tach_count * poles)

        return rpm

    # =============================================================================
    # Public API - PWM Control
    # =============================================================================

    def set_pwm_duty_cycle(self, channel: int, percent: float) -> None:
        """
        Set PWM duty cycle for direct PWM control mode.

        Args:
            channel: Fan channel number (1-5)
            percent: PWM duty cycle percentage (0-100)

        Raises:
            ValueError: If channel or percent is out of range
            EMC2305Error: If I2C communication fails

        Example:
            >>> fan_controller.set_pwm_duty_cycle(1, 75.0)  # Set fan 1 to 75%
        """
        self._validate_channel(channel)
        self._validate_percent(percent)

        with self._lock:
            try:
                # Calculate register address
                reg = const.REG_FAN1_SETTING + (channel - 1) * const.FAN_CHANNEL_OFFSET

                # Convert percent to PWM value
                pwm_value = self._percent_to_pwm(percent)

                # Write to Fan Setting register
                self.i2c_bus.write_byte(self.address, reg, pwm_value)

                logger.debug(f"Fan {channel} PWM set to {percent:.1f}% (0x{pwm_value:02X})")

            except I2CError as e:
                raise EMC2305Error(f"Failed to set PWM for fan {channel}: {e}")

    def get_pwm_duty_cycle(self, channel: int) -> float:
        """
        Get current PWM duty cycle.

        Args:
            channel: Fan channel number (1-5)

        Returns:
            PWM duty cycle percentage (0-100)

        Example:
            >>> duty_cycle = fan_controller.get_pwm_duty_cycle(1)
            >>> print(f"Fan 1 is at {duty_cycle}%")
        """
        self._validate_channel(channel)

        with self._lock:
            try:
                # Calculate register address
                reg = const.REG_FAN1_SETTING + (channel - 1) * const.FAN_CHANNEL_OFFSET

                # Read Fan Setting register
                pwm_value = self.i2c_bus.read_byte(self.address, reg)

                # Convert to percent
                percent = self._pwm_to_percent(pwm_value)

                return percent

            except I2CError as e:
                raise EMC2305Error(f"Failed to read PWM for fan {channel}: {e}")

    # =============================================================================
    # Public API - RPM Control (FSC Mode)
    # =============================================================================

    def set_target_rpm(self, channel: int, rpm: int) -> None:
        """
        Set target RPM for FSC (closed-loop) control mode.

        The EMC2305's PID controller will automatically adjust PWM to maintain this RPM.

        Args:
            channel: Fan channel number (1-5)
            rpm: Target RPM (500-16000 with internal clock)

        Raises:
            ValueError: If channel or RPM is out of range
            EMC2305Error: If I2C communication fails

        Example:
            >>> fan_controller.set_target_rpm(1, 3000)  # Set fan 1 to 3000 RPM
        """
        self._validate_channel(channel)

        max_rpm = const.MAX_RPM_EXT_CLOCK if self.use_external_clock else const.MAX_RPM
        self._validate_rpm(rpm, const.MIN_RPM, max_rpm)

        with self._lock:
            try:
                # Convert RPM to TACH count
                tach_count = self._rpm_to_tach_count(rpm)

                # Calculate register addresses
                base = const.REG_FAN1_SETTING + (channel - 1) * const.FAN_CHANNEL_OFFSET
                reg_low = base + (const.REG_FAN1_TACH_TARGET_LOW - const.REG_FAN1_SETTING)
                reg_high = base + (const.REG_FAN1_TACH_TARGET_HIGH - const.REG_FAN1_SETTING)

                # Write TACH target (13-bit value, MSB first)
                self.i2c_bus.write_byte(self.address, reg_high, (tach_count >> const.TACH_COUNT_HIGH_SHIFT) & const.TACH_COUNT_HIGH_MASK)
                self.i2c_bus.write_byte(self.address, reg_low, tach_count & const.BYTE_MASK)

                logger.debug(
                    f"Fan {channel} target RPM set to {rpm} (TACH count: 0x{tach_count:04X})"
                )

            except I2CError as e:
                raise EMC2305Error(f"Failed to set target RPM for fan {channel}: {e}")

    def get_target_rpm(self, channel: int) -> int:
        """
        Get target RPM setting for FSC mode.

        Args:
            channel: Fan channel number (1-5)

        Returns:
            Target RPM value

        Example:
            >>> target = fan_controller.get_target_rpm(1)
            >>> print(f"Fan 1 target: {target} RPM")
        """
        self._validate_channel(channel)

        with self._lock:
            try:
                # Calculate register addresses
                base = const.REG_FAN1_SETTING + (channel - 1) * const.FAN_CHANNEL_OFFSET
                reg_low = base + (const.REG_FAN1_TACH_TARGET_LOW - const.REG_FAN1_SETTING)
                reg_high = base + (const.REG_FAN1_TACH_TARGET_HIGH - const.REG_FAN1_SETTING)

                # Read TACH target (13-bit value)
                tach_high = self.i2c_bus.read_byte(self.address, reg_high) & const.TACH_COUNT_HIGH_MASK
                tach_low = self.i2c_bus.read_byte(self.address, reg_low)
                tach_count = (tach_high << const.TACH_COUNT_HIGH_SHIFT) | tach_low

                # Convert to RPM
                config = self._fan_configs.get(channel, FanConfig())
                rpm = self._tach_count_to_rpm(tach_count, config.edges)

                return rpm

            except I2CError as e:
                raise EMC2305Error(f"Failed to read target RPM for fan {channel}: {e}")

    def get_current_rpm(self, channel: int) -> int:
        """
        Get current measured RPM from tachometer.

        Args:
            channel: Fan channel number (1-5)

        Returns:
            Current RPM value (0 if fan is stalled)

        Example:
            >>> rpm = fan_controller.get_current_rpm(1)
            >>> print(f"Fan 1 speed: {rpm} RPM")
        """
        self._validate_channel(channel)

        with self._lock:
            try:
                # Calculate register addresses
                base = const.REG_FAN1_SETTING + (channel - 1) * const.FAN_CHANNEL_OFFSET
                reg_low = base + (const.REG_FAN1_TACH_READING_LOW - const.REG_FAN1_SETTING)
                reg_high = base + (const.REG_FAN1_TACH_READING_HIGH - const.REG_FAN1_SETTING)

                # Read TACH reading (13-bit value)
                tach_high = self.i2c_bus.read_byte(self.address, reg_high) & const.TACH_COUNT_HIGH_MASK
                tach_low = self.i2c_bus.read_byte(self.address, reg_low)
                tach_count = (tach_high << const.TACH_COUNT_HIGH_SHIFT) | tach_low

                # Convert to RPM
                config = self._fan_configs.get(channel, FanConfig())
                rpm = self._tach_count_to_rpm(tach_count, config.edges)

                return rpm

            except I2CError as e:
                raise EMC2305Error(f"Failed to read RPM for fan {channel}: {e}")

    # =============================================================================
    # Public API - Fan Configuration
    # =============================================================================

    def configure_fan(self, channel: int, config: FanConfig) -> None:
        """
        Configure a fan channel with custom settings.

        Args:
            channel: Fan channel number (1-5)
            config: Fan configuration

        Example:
            >>> config = FanConfig(
            ...     control_mode=ControlMode.FSC,
            ...     min_rpm=1000,
            ...     max_rpm=4000,
            ...     pid_gain_p=4,
            ...     pid_gain_i=2,
            ...     pid_gain_d=1
            ... )
            >>> fan_controller.configure_fan(1, config)
        """
        self._validate_channel(channel)
        self._validate_fan_config(config)
        self._check_not_locked()

        with self._lock:
            self._fan_configs[channel] = config
            self._configure_fan_registers(channel, config)

        logger.info(f"Fan {channel} configured with custom settings")

    def set_control_mode(self, channel: int, mode: ControlMode) -> None:
        """
        Set control mode for a fan channel.

        Args:
            channel: Fan channel number (1-5)
            mode: Control mode (PWM or FSC)

        Example:
            >>> fan_controller.set_control_mode(1, ControlMode.FSC)
        """
        self._validate_channel(channel)
        self._check_not_locked()

        with self._lock:
            config = self._fan_configs.get(channel, FanConfig())
            config.control_mode = mode
            self._fan_configs[channel] = config
            self._configure_fan_registers(channel, config)

        logger.info(f"Fan {channel} control mode set to {mode.value}")

    # =============================================================================
    # Public API - Status and Monitoring
    # =============================================================================

    def get_fan_status(self, channel: int) -> FanStatus:
        """
        Get operational status of a fan channel.

        Args:
            channel: Fan channel number (1-5)

        Returns:
            Fan status

        Example:
            >>> status = fan_controller.get_fan_status(1)
            >>> if status == FanStatus.STALLED:
            ...     print("Fan 1 is stalled!")
        """
        self._validate_channel(channel)

        with self._lock:
            try:
                channel_bit = 1 << (channel - 1)

                # Read all status registers in one optimized I2C transaction
                _, stall_status, spin_status, drive_status = self._read_all_status_registers()

                # Check stall status
                if stall_status & channel_bit:
                    return FanStatus.STALLED

                # Check spin failure
                if spin_status & channel_bit:
                    return FanStatus.SPIN_FAILURE

                # Check drive failure (aging fan)
                if drive_status & channel_bit:
                    return FanStatus.DRIVE_FAILURE

                return FanStatus.OK

            except I2CError as e:
                logger.error(f"Failed to read status for fan {channel}: {e}")
                return FanStatus.UNKNOWN

    def get_all_fan_states(self) -> Dict[int, FanState]:
        """
        Get current state of all fan channels.

        Returns:
            Dictionary mapping channel number to FanState

        Example:
            >>> states = fan_controller.get_all_fan_states()
            >>> for channel, state in states.items():
            ...     print(f"Fan {channel}: {state.current_rpm} RPM, {state.status}")
        """
        states = {}

        for channel in range(1, const.NUM_FAN_CHANNELS + 1):
            config = self._fan_configs.get(channel, FanConfig())

            state = FanState(
                channel=channel,
                enabled=config.enabled,
                control_mode=config.control_mode,
                pwm_percent=self.get_pwm_duty_cycle(channel),
                target_rpm=self.get_target_rpm(channel) if config.control_mode == ControlMode.FSC else 0,
                current_rpm=self.get_current_rpm(channel),
                status=self.get_fan_status(channel),
            )

            states[channel] = state

        return states

    def get_product_features(self) -> ProductFeatures:
        """
        Read product features and device identification.

        Returns hardware capabilities including number of fan channels,
        RPM control support, product ID, manufacturer ID, and revision.

        Returns:
            ProductFeatures dataclass with device information

        Raises:
            EMC2305CommunicationError: If I2C communication fails

        Example:
            >>> features = fan_controller.get_product_features()
            >>> print(f"Device: EMC230{features.fan_channels}")
            >>> print(f"Product ID: 0x{features.product_id:02X}")
            >>> print(f"RPM Control: {features.rpm_control_supported}")
        """
        try:
            # Read Product Features register (0xFC)
            features_reg = self.i2c_bus.read_byte(self.address, const.REG_PRODUCT_FEATURES)
            fan_channels = features_reg & const.PRODUCT_FEATURES_FAN_COUNT_MASK
            rpm_control = bool(features_reg & const.PRODUCT_FEATURES_RPM_CONTROL)

            # Read identification registers
            product_id = self.i2c_bus.read_byte(self.address, const.REG_PRODUCT_ID)
            mfg_id = self.i2c_bus.read_byte(self.address, const.REG_MANUFACTURER_ID)
            revision = self.i2c_bus.read_byte(self.address, const.REG_REVISION)

            return ProductFeatures(
                fan_channels=fan_channels,
                rpm_control_supported=rpm_control,
                product_id=product_id,
                manufacturer_id=mfg_id,
                revision=revision,
            )

        except I2CError as e:
            raise EMC2305CommunicationError(f"Failed to read product features: {e}")

    def check_watchdog(self) -> bool:
        """
        Check if watchdog timeout has occurred.

        Returns:
            True if watchdog timeout occurred

        Example:
            >>> if fan_controller.check_watchdog():
            ...     print("Watchdog timeout detected!")
        """
        try:
            status = self.i2c_bus.read_byte(self.address, const.REG_FAN_STATUS)
            return bool(status & const.FAN_STATUS_WATCH)
        except I2CError as e:
            logger.error(f"Failed to check watchdog status: {e}")
            return False

    def reset_watchdog(self) -> None:
        """
        Reset the watchdog timer by performing a dummy write.

        Call this periodically (within 4 seconds) to prevent watchdog timeout.

        Example:
            >>> fan_controller.reset_watchdog()
        """
        if self.enable_watchdog:
            try:
                # Read configuration register (any read/write resets watchdog)
                self.i2c_bus.read_byte(self.address, const.REG_CONFIGURATION)
                logger.debug("Watchdog timer reset")
            except I2CError as e:
                logger.error(f"Failed to reset watchdog: {e}")

    # =============================================================================
    # Public API - Software Lock
    # =============================================================================

    def lock_configuration(self) -> None:
        """
        Lock configuration registers to prevent accidental modification.

        WARNING: Once locked, configuration registers become read-only until
        hardware reset. This is an irreversible operation that protects
        production deployments from configuration changes.

        Use this in production environments after configuration is finalized.

        Raises:
            EMC2305Error: If lock operation fails

        Example:
            >>> fan_controller.configure_fan(1, my_config)
            >>> fan_controller.lock_configuration()  # Prevent changes
        """
        try:
            # Write SOFTWARE_LOCK_LOCKED_VALUE to lock register (irreversible until reset)
            self.i2c_bus.write_byte(
                self.address,
                const.REG_SOFTWARE_LOCK,
                const.SOFTWARE_LOCK_LOCKED_VALUE
            )
            self._is_locked = True
            logger.warning(
                "Configuration registers LOCKED - changes disabled until hardware reset"
            )
        except I2CError as e:
            raise EMC2305Error(f"Failed to lock configuration: {e}")

    def is_configuration_locked(self) -> bool:
        """
        Check if configuration registers are locked.

        Returns:
            True if configuration is locked, False otherwise

        Example:
            >>> if fan_controller.is_configuration_locked():
            ...     print("Configuration is protected")
        """
        try:
            # Read lock register - SOFTWARE_LOCK_LOCKED_VALUE means locked
            lock_status = self.i2c_bus.read_byte(self.address, const.REG_SOFTWARE_LOCK)
            self._is_locked = (lock_status == const.SOFTWARE_LOCK_LOCKED_VALUE)
            return self._is_locked
        except I2CError as e:
            logger.error(f"Failed to read lock status: {e}")
            return self._is_locked  # Return cached status on error

    def _check_not_locked(self) -> None:
        """
        Internal method to verify configuration is not locked.

        Always reads from hardware register to avoid race conditions.

        Raises:
            EMC2305ConfigurationLockedError: If configuration is locked
        """
        if self.is_configuration_locked():
            raise EMC2305ConfigurationLockedError(
                "Configuration registers are locked. Hardware reset required to unlock. "
                "This prevents accidental changes in production environments."
            )

    # =============================================================================
    # Public API - Alert/Interrupt Handling
    # =============================================================================

    def configure_fan_alerts(self, channel: int, enabled: bool) -> None:
        """
        Enable or disable ALERT# pin assertion for a specific fan.

        When enabled, fan faults (stall, spin failure, drive failure) will
        assert the ALERT# pin (active low) and trigger SMBus Alert Response.

        Args:
            channel: Fan channel number (1-5)
            enabled: True to enable alerts, False to disable

        Raises:
            EMC2305ValidationError: If channel is invalid
            EMC2305CommunicationError: If I2C communication fails

        Example:
            >>> fan_controller.configure_fan_alerts(1, True)  # Enable alerts for fan 1
            >>> fan_controller.configure_fan_alerts(2, False) # Disable alerts for fan 2
        """
        self._validate_channel(channel)

        try:
            with self._lock:
                # Read current interrupt enable register
                int_enable = self.i2c_bus.read_byte(self.address, const.REG_FAN_INTERRUPT_ENABLE)

                # Modify the bit for this channel
                channel_bit = 1 << (channel - 1)
                if enabled:
                    int_enable |= channel_bit
                else:
                    int_enable &= ~channel_bit

                # Write back
                self.i2c_bus.write_byte(self.address, const.REG_FAN_INTERRUPT_ENABLE, int_enable)

                logger.debug(f"Fan {channel} alerts {'enabled' if enabled else 'disabled'}")

        except I2CError as e:
            raise EMC2305CommunicationError(f"Failed to configure fan alerts: {e}")

    def get_alert_status(self) -> Dict[int, bool]:
        """
        Get alert status for all fan channels.

        Returns which fans have active fault conditions that would
        assert the ALERT# pin (if alerts are enabled for those fans).

        Returns:
            Dictionary mapping channel number to alert status (True = alert active)

        Raises:
            EMC2305CommunicationError: If I2C communication fails

        Example:
            >>> alerts = fan_controller.get_alert_status()
            >>> for channel, has_alert in alerts.items():
            ...     if has_alert:
            ...         print(f"Fan {channel} has an alert!")
        """
        try:
            with self._lock:
                # Read all status registers in one optimized I2C transaction
                _, stall_status, spin_status, drive_fail_status = self._read_all_status_registers()

                # Build alert status for each channel
                alerts = {}
                for channel in range(1, const.NUM_FAN_CHANNELS + 1):
                    channel_bit = 1 << (channel - 1)

                    # Channel has alert if any fault condition is active
                    has_fault = (
                        (stall_status & channel_bit) or
                        (spin_status & channel_bit) or
                        (drive_fail_status & channel_bit)
                    )

                    alerts[channel] = bool(has_fault)

                return alerts

        except I2CError as e:
            raise EMC2305CommunicationError(f"Failed to read alert status: {e}")

    def is_alert_active(self) -> bool:
        """
        Check if ALERT# pin is currently asserted.

        The ALERT# pin is asserted (low) when any enabled fan has a fault condition.

        Returns:
            True if ALERT# pin is asserted, False otherwise

        Raises:
            EMC2305CommunicationError: If I2C communication fails

        Example:
            >>> if fan_controller.is_alert_active():
            ...     alerts = fan_controller.get_alert_status()
            ...     print(f"Active alerts: {alerts}")
        """
        try:
            with self._lock:
                # Check if any fan has an active alert
                fan_status = self.i2c_bus.read_byte(self.address, const.REG_FAN_STATUS)

                # Fan status bits indicate various conditions that assert ALERT#
                # Bits 0-4: Per-fan alerts
                alert_bits = fan_status & const.FAN_INTERRUPT_ENABLE_ALL_FANS  # Check bits 0-4 for fans 1-5

                return alert_bits != 0

        except I2CError as e:
            raise EMC2305CommunicationError(f"Failed to check alert status: {e}")

    def clear_alert_status(self) -> None:
        """
        Clear all alert/fault status flags.

        Reading the status registers clears the latched fault conditions
        and de-asserts the ALERT# pin (if no new faults are present).

        This implements the SMBus Alert Response Address (ARA) protocol
        at the application level.

        Raises:
            EMC2305CommunicationError: If I2C communication fails

        Example:
            >>> fan_controller.clear_alert_status()  # Clear all alerts
            >>> # ALERT# pin will de-assert if no active faults remain
        """
        try:
            with self._lock:
                # Reading status registers clears them (per EMC2305 datasheet)
                self.i2c_bus.read_byte(self.address, const.REG_FAN_STATUS)
                self.i2c_bus.read_byte(self.address, const.REG_FAN_STALL_STATUS)
                self.i2c_bus.read_byte(self.address, const.REG_FAN_SPIN_STATUS)
                self.i2c_bus.read_byte(self.address, const.REG_DRIVE_FAIL_STATUS)

                logger.debug("Alert status cleared for all fans")

        except I2CError as e:
            raise EMC2305CommunicationError(f"Failed to clear alert status: {e}")

    # =============================================================================
    # Public API - Utility
    # =============================================================================

    def close(self) -> None:
        """
        Close the fan controller and release resources.

        Sets all fans to safe state before closing.
        """
        logger.info("Closing EMC2305 fan controller")

        # Set all fans to minimum safe speed
        for channel in range(1, const.NUM_FAN_CHANNELS + 1):
            try:
                self.set_pwm_duty_cycle(channel, const.SAFE_SHUTDOWN_PWM_PERCENT)  # Safe PWM for controlled shutdown
            except Exception as e:
                logger.error(f"Failed to set fan {channel} to safe state: {e}")

    def __enter__(self) -> 'EMC2305':
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Optional[Any]) -> bool:
        """Context manager exit."""
        self.close()
        return False

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"EMC2305(address=0x{self.address:02X}, "
            f"product_id=0x{self.product_id:02X}, "
            f"revision=0x{self.revision:02X})"
        )
