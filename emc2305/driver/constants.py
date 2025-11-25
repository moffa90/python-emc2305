# Copyright (c) 2025 Contributors to the microchip-emc2305 project
# SPDX-License-Identifier: MIT

"""
EMC2305 Hardware Constants

Register addresses, timing constants, and hardware-specific values for the
SMSC/Microchip EMC2305 5-Channel PWM Fan Controller.

Based on EMC2305 datasheet DS20006532A (April 2021)
"""

# =============================================================================
# Device Identification
# =============================================================================

PRODUCT_ID = 0x34
"""Expected Product ID for EMC2305"""

MANUFACTURER_ID = 0x5D
"""Expected Manufacturer ID (SMSC)"""

REVISION_REG = 0xFF
"""Register address for chip revision"""

# Product Features Register Bit Masks (REG_PRODUCT_FEATURES = 0xFC)
PRODUCT_FEATURES_FAN_COUNT_MASK = 0x07
"""Bits 0-2: Number of fan channels (0-7)"""

PRODUCT_FEATURES_RPM_CONTROL = 0x08
"""Bit 3: RPM-based fan speed control supported"""

# =============================================================================
# I2C Bus Configuration
# =============================================================================

DEFAULT_I2C_BUS = 0
"""Default I2C bus number"""

DEFAULT_DEVICE_ADDRESS = 0x61
"""Default I2C device address (configurable via ADDR_SEL pin)"""

SUPPORTED_ADDRESSES = [0x4C, 0x4D, 0x5C, 0x5D, 0x5E, 0x5F]
"""All possible EMC2305 I2C addresses (via ADDR_SEL pin configuration)"""

DEFAULT_I2C_LOCK_TIMEOUT = 5.0
"""Default I2C bus lock timeout in seconds"""

DEFAULT_I2C_LOCK_PATH = "/var/lock"
"""Default path for I2C bus lock files"""

# I2C/SMBus Protocol Limits
MIN_I2C_ADDRESS = 0x00
"""Minimum valid 7-bit I2C address"""

MAX_I2C_ADDRESS = 0x7F
"""Maximum valid 7-bit I2C address"""

MIN_REGISTER_ADDRESS = 0x00
"""Minimum register address"""

MAX_REGISTER_ADDRESS = 0xFF
"""Maximum register address (8-bit)"""

SMBUS_BLOCK_MAX_LENGTH = 32
"""Maximum block read/write length for SMBus protocol"""

# =============================================================================
# Global Configuration Registers
# =============================================================================

REG_CONFIGURATION = 0x20
"""Configuration register - watchdog, clock selection, alert modes"""

REG_FAN_STATUS = 0x24
"""Fan Status register - combined status for all fans"""

REG_FAN_STALL_STATUS = 0x25
"""Fan Stall Status register - per-fan stall flags"""

REG_FAN_SPIN_STATUS = 0x26
"""Fan Spin Status register - per-fan spin-up failure flags"""

REG_DRIVE_FAIL_STATUS = 0x27
"""Drive Fail Status register - per-fan drive failure flags (aging fans)"""

REG_FAN_INTERRUPT_ENABLE = 0x29
"""Fan Interrupt Enable register - enable alerts per fan"""

REG_PWM_POLARITY_CONFIG = 0x2A
"""PWM Polarity Configuration - normal or inverted per fan"""

REG_PWM_OUTPUT_CONFIG = 0x2B
"""PWM Output Configuration - open-drain or push-pull per fan"""

# Default PWM configuration values
DEFAULT_PWM_POLARITY = 0x00
"""Default PWM polarity configuration (normal/non-inverted for all channels)"""

DEFAULT_PWM_OUTPUT_CONFIG = 0x00
"""Default PWM output configuration (open-drain for all channels, per datasheet default)"""

# PWM Output Type Constants (Register 0x2B bit values)
# Datasheet: '0' (default) = open drain, '1' = push-pull
PWM_OUTPUT_OPEN_DRAIN = 0
"""Open-drain output mode (default, requires external pull-up resistor)"""

PWM_OUTPUT_PUSH_PULL = 1
"""Push-pull output mode (active drive high and low)"""

FAN_INTERRUPT_ENABLE_ALL_FANS = 0x1F
"""Enable interrupts for all 5 fan channels (bits 4-0 set)"""

REG_PWM_BASE_FREQ_1 = 0x2C
"""PWM Base Frequency 1 - fans 1-3"""

REG_PWM_BASE_FREQ_2 = 0x2D
"""PWM Base Frequency 2 - fans 4-5"""

REG_SOFTWARE_LOCK = 0xEF
"""Software Lock register - write 0x00 to unlock, 0xFF to lock"""

# Software Lock register values
SOFTWARE_LOCK_LOCKED_VALUE = 0xFF
"""Value to write to REG_SOFTWARE_LOCK to lock configuration (irreversible until reset)"""

SOFTWARE_LOCK_UNLOCKED_VALUE = 0x00
"""Value read from REG_SOFTWARE_LOCK when configuration is unlocked"""

REG_PRODUCT_FEATURES = 0xFC
"""Product Features register - indicates device capabilities (read-only)"""

REG_PRODUCT_ID = 0xFD
"""Product ID register (should read 0x34)"""

REG_MANUFACTURER_ID = 0xFE
"""Manufacturer ID register (should read 0x5D)"""

REG_REVISION = 0xFF
"""Chip revision register"""

# =============================================================================
# Per-Fan Channel Registers (Base addresses for Fan 1)
# =============================================================================
# Fan channels 2-5 use the same register offsets + (channel_number * 0x10)
# Example: Fan 2 Setting = 0x30 + 0x10 = 0x40
#          Fan 3 Setting = 0x30 + 0x20 = 0x50
#          Fan 4 Setting = 0x30 + 0x30 = 0x60
#          Fan 5 Setting = 0x30 + 0x40 = 0x70

FAN_CHANNEL_OFFSET = 0x10
"""Offset between fan channel register sets"""

NUM_FAN_CHANNELS = 5
"""Number of fan channels (1-5)"""

# Fan 1 base register addresses (0x30-0x3F)
REG_FAN1_SETTING = 0x30
"""Fan 1 Setting - PWM duty cycle (0-255) or max drive in FSC mode"""

REG_FAN1_PWM_DIVIDE = 0x31
"""Fan 1 PWM Divide - divides base frequency (1-255)"""

REG_FAN1_CONFIG1 = 0x32
"""Fan 1 Configuration 1 - control mode, range, edges, update rate"""

REG_FAN1_CONFIG2 = 0x33
"""Fan 1 Configuration 2 - error range, derivative mode, glitch filter"""

REG_FAN1_GAIN = 0x35
"""Fan 1 Gain - combined PID gain settings (datasheet pp. 42-43)"""

REG_FAN1_SPIN_UP_CONFIG = 0x36
"""Fan 1 Spin Up Configuration - spin level and time"""

REG_FAN1_MAX_STEP = 0x37
"""Fan 1 Max Step - maximum drive change per update"""

REG_FAN1_MINIMUM_DRIVE = 0x38
"""Fan 1 Minimum Drive - prevents stall oscillation"""

REG_FAN1_VALID_TACH_COUNT = 0x39
"""Fan 1 Valid TACH Count - minimum valid tachometer count (MSB only, single 8-bit register)"""

REG_FAN1_DRIVE_FAIL_BAND_LOW = 0x3A
"""Fan 1 Drive Fail Band Low - CRITICAL: Confirmed by testing to be 0x3A (not 0x3B as in some datasheets)"""

REG_FAN1_DRIVE_FAIL_BAND_HIGH = 0x3B
"""Fan 1 Drive Fail Band High - CRITICAL: Confirmed by testing to be 0x3B (not 0x3C as in some datasheets)"""

REG_FAN1_TACH_TARGET_LOW = 0x3C
"""Fan 1 TACH Target Low - target RPM for FSC mode (LSB)"""

REG_FAN1_TACH_TARGET_HIGH = 0x3D
"""Fan 1 TACH Target High - target RPM for FSC mode (MSB)"""

REG_FAN1_TACH_READING_HIGH = 0x3E
"""Fan 1 TACH Reading High - current RPM measurement (MSB)"""

REG_FAN1_TACH_READING_LOW = 0x3F
"""Fan 1 TACH Reading Low - current RPM measurement (LSB)"""

# =============================================================================
# Configuration Register Bit Masks (REG_CONFIGURATION = 0x20)
# =============================================================================

CONFIG_MASK_MASK = 0x80
"""MASK bit - 1=disable ALERT# pin"""

CONFIG_DIS_TO = 0x40
"""DIS_TO bit - 1=disable SMBus timeout (recommended for full I2C compliance)"""

CONFIG_WD_EN = 0x20
"""WD_EN bit - 1=enable watchdog timer (4 second timeout)"""

CONFIG_DR_EXT_CLK = 0x10
"""DR_EXT_CLK bit - 1=drive external clock on CLK pin"""

CONFIG_USE_EXT_CLK = 0x08
"""USE_EXT_CLK bit - 1=use external clock (must be 32.768 kHz)"""

CONFIG_CLK_SEL = 0x04
"""CLK_SEL bit - clock selection (see datasheet)"""

CONFIG_GLBL_EN = 0x02
"""GLBL_EN bit - CRITICAL: Must be enabled (1) for PWM outputs to work. Without this, all PWM outputs are disabled."""

CONFIG_GPO = 0x01
"""GPO bit - general purpose output via ALERT# pin"""

# =============================================================================
# Fan Configuration Register 1 Bit Masks (REG_FANx_CONFIG1 = 0x32 + offset)
# =============================================================================

FAN_CONFIG1_UPDATE_MASK = 0xE0
"""Update time field mask (bits 7-5)"""

FAN_CONFIG1_UPDATE_100MS = 0x00
"""Update time: 100ms"""

FAN_CONFIG1_UPDATE_200MS = 0x20
"""Update time: 200ms"""

FAN_CONFIG1_UPDATE_300MS = 0x40
"""Update time: 300ms"""

FAN_CONFIG1_UPDATE_400MS = 0x60
"""Update time: 400ms"""

FAN_CONFIG1_UPDATE_500MS = 0x80
"""Update time: 500ms"""

FAN_CONFIG1_UPDATE_800MS = 0xA0
"""Update time: 800ms"""

FAN_CONFIG1_UPDATE_1200MS = 0xC0
"""Update time: 1200ms"""

FAN_CONFIG1_UPDATE_1600MS = 0xE0
"""Update time: 1600ms"""

FAN_CONFIG1_EDGES_MASK = 0x18
"""Tachometer edges field mask (bits 4-3)"""

FAN_CONFIG1_EDGES_3 = 0x00
"""3 edges per revolution (1-pole fan)"""

FAN_CONFIG1_EDGES_5 = 0x08
"""5 edges per revolution (2-pole fan)"""

FAN_CONFIG1_EDGES_7 = 0x10
"""7 edges per revolution (3-pole fan)"""

FAN_CONFIG1_EDGES_9 = 0x18
"""9 edges per revolution (4-pole fan)"""

FAN_CONFIG1_RANGE_MASK = 0x60
"""RPM range field mask (bits 6-5) - used in CONFIG2, included here for reference"""

FAN_CONFIG1_RANGE_500_16K = 0x00
"""RPM range: 500-16,000 RPM"""

FAN_CONFIG1_RANGE_1K_32K = 0x20
"""RPM range: 1,000-32,000 RPM (requires external clock)"""

FAN_CONFIG1_EN_ALGO = 0x04
"""EN_ALGO bit - 1=enable RPM-based Fan Speed Control algorithm (FSC mode)"""

FAN_CONFIG1_EN_RRC = 0x02
"""EN_RRC bit - 1=enable Ramp Rate Control"""

FAN_CONFIG1_CLR = 0x01
"""CLR bit - write 1 to clear accumulator errors"""

# =============================================================================
# Fan Configuration Register 2 Bit Masks (REG_FANx_CONFIG2 = 0x33 + offset)
# =============================================================================

FAN_CONFIG2_ERR_RNG_MASK = 0xC0
"""Error range field mask (bits 7-6)"""

FAN_CONFIG2_ERR_RNG_0 = 0x00
"""Error range: No windowing (±0 RPM)"""

FAN_CONFIG2_ERR_RNG_50 = 0x40
"""Error range: ±50 RPM window"""

FAN_CONFIG2_ERR_RNG_100 = 0x80
"""Error range: ±100 RPM window"""

FAN_CONFIG2_ERR_RNG_200 = 0xC0
"""Error range: ±200 RPM window"""

FAN_CONFIG2_DER_OPT_MASK = 0x38
"""Derivative option field mask (bits 5-3)"""

FAN_CONFIG2_DER_OPT_NONE = 0x00
"""Derivative: Basic derivative of error"""

FAN_CONFIG2_DER_OPT_1 = 0x08
"""Derivative option 1 (see datasheet Section 3.3.4)"""

FAN_CONFIG2_DER_OPT_2 = 0x10
"""Derivative option 2 (see datasheet Section 3.3.4)"""

FAN_CONFIG2_DER_OPT_3 = 0x18
"""Derivative option 3 (see datasheet Section 3.3.4)"""

FAN_CONFIG2_DER_OPT_4 = 0x20
"""Derivative option 4 (see datasheet Section 3.3.4)"""

FAN_CONFIG2_DER_OPT_5 = 0x28
"""Derivative option 5 (see datasheet Section 3.3.4)"""

FAN_CONFIG2_DER_OPT_6 = 0x30
"""Derivative option 6 (see datasheet Section 3.3.4)"""

FAN_CONFIG2_DER_OPT_7 = 0x38
"""Derivative option 7 (see datasheet Section 3.3.4)"""

FAN_CONFIG2_GLITCH_EN = 0x04
"""GLITCH_EN bit - 1=enable tachometer glitch filtering"""

FAN_CONFIG2_RNG_MASK = 0x60
"""RPM range field mask (bits 6-5) - typically set in CONFIG2"""

FAN_CONFIG2_RNG_500_16K = 0x00
"""RPM range: 500-16,000 RPM"""

FAN_CONFIG2_RNG_1K_32K = 0x20
"""RPM range: 1,000-32,000 RPM (requires external clock)"""

# =============================================================================
# PWM Frequency Configuration
# =============================================================================

PWM_FREQ_26000HZ = 0x00
"""26 kHz base frequency"""

PWM_FREQ_19531HZ = 0x01
"""19.531 kHz base frequency"""

PWM_FREQ_4882HZ = 0x02
"""4.882 kHz base frequency"""

PWM_FREQ_2441HZ = 0x03
"""2.441 kHz base frequency"""

# PWM frequency selection thresholds (for automatic frequency selection)
PWM_FREQ_26000HZ_THRESHOLD = 20000
"""Threshold for selecting 26 kHz base frequency (freq >= 20000 Hz)"""

PWM_FREQ_19531HZ_THRESHOLD = 12000
"""Threshold for selecting 19.531 kHz base frequency (12000 Hz <= freq < 20000 Hz)"""

PWM_FREQ_4882HZ_THRESHOLD = 3500
"""Threshold for selecting 4.882 kHz base frequency (3500 Hz <= freq < 12000 Hz)"""

# PWM divide values (1-255) further divide the base frequency
# Final PWM frequency = Base Frequency / PWM_DIVIDE
DEFAULT_PWM_DIVIDE = 1
"""Default PWM divide value (no division)"""

# Valid PWM divide values (hardware-supported divisors)
VALID_PWM_DIVIDES = [1, 2, 4, 8, 16, 32]
"""Recommended PWM divide values for standard operation"""

# =============================================================================
# Spin-Up Configuration
# =============================================================================

SPIN_UP_TIME_MASK = 0x1F
"""Spin-up time mask (bits 4-0)"""

SPIN_UP_TIME_UNIT_MS = 50
"""Spin-up time unit in milliseconds (each count = 50ms)"""

SPIN_UP_TIME_MAX_VALUE = 31
"""Maximum spin-up time value (0-31)"""

SPIN_UP_LEVEL_MASK = 0xE0
"""Spin-up drive level mask (bits 7-5)"""

SPIN_UP_LEVEL_30_PERCENT = 0x00
"""30% drive level during spin-up"""

SPIN_UP_LEVEL_35_PERCENT = 0x20
"""35% drive level during spin-up"""

SPIN_UP_LEVEL_40_PERCENT = 0x40
"""40% drive level during spin-up"""

SPIN_UP_LEVEL_45_PERCENT = 0x60
"""45% drive level during spin-up"""

SPIN_UP_LEVEL_50_PERCENT = 0x80
"""50% drive level during spin-up"""

SPIN_UP_LEVEL_55_PERCENT = 0xA0
"""55% drive level during spin-up"""

SPIN_UP_LEVEL_60_PERCENT = 0xC0
"""60% drive level during spin-up"""

SPIN_UP_LEVEL_65_PERCENT = 0xE0
"""65% drive level during spin-up"""

# Spin-up time values (0-31) * 0.05s = 0 to 1.55 seconds
# Time = value * 50ms
DEFAULT_SPIN_UP_TIME = 10  # 10 * 50ms = 500ms
"""Default spin-up time (10 = 500ms)"""

# =============================================================================
# Fan Speed and RPM Limits
# =============================================================================

MIN_FAN_SPEED_PERCENT = 0
"""Minimum fan speed percentage"""

MAX_FAN_SPEED_PERCENT = 100
"""Maximum fan speed percentage"""

MIN_PWM_VALUE = 0
"""Minimum PWM register value (0 = 0%)"""

MAX_PWM_VALUE = 255
"""Maximum PWM register value (255 = 100%)"""

SAFE_SHUTDOWN_PWM_PERCENT = 30
"""Safe PWM percentage for controlled fan shutdown (prevents abrupt stop)"""

MIN_RPM = 500
"""Minimum supported RPM (hardware limit)"""

MIN_VALID_RPM_READING = 200
"""RPM readings below this threshold are considered noise (fan stopped)"""

MAX_RPM = 16000
"""Maximum supported RPM with internal clock (500-16k range)"""

MAX_RPM_EXT_CLOCK = 32000
"""Maximum supported RPM with external clock (1k-32k range)"""

# =============================================================================
# RPM Calculation Constants
# =============================================================================

# RPM calculation: RPM = (TACH_FREQ * 60) / (TACH_COUNT * poles)
# Where TACH_FREQ depends on clock source

INTERNAL_CLOCK_FREQ_HZ = 32000
"""Internal oscillator frequency (nominally 32 kHz)"""

EXTERNAL_CLOCK_FREQ_HZ = 32768
"""External clock frequency (32.768 kHz crystal)"""

TACH_COUNT_MAX = 0x1FFF
"""Maximum tachometer count value (13-bit)"""

TACH_COUNT_STOPPED_THRESHOLD = 1000
"""Tach count threshold for detecting stopped fan (after 3-bit shift).
EMC2305 returns near-max values (e.g., 1022) when no tach signal is detected."""

# Minimum valid TACH count - fan is considered stalled below this
DEFAULT_VALID_TACH_COUNT = 0x0FFF
"""Default minimum valid tachometer count for stall detection"""

# =============================================================================
# Bit Manipulation Constants
# =============================================================================

# Common bit masks
BYTE_MASK = 0xFF
"""Mask for extracting a single byte (8 bits)"""

TACH_COUNT_HIGH_MASK = 0x1F
"""Mask for high 5 bits of 13-bit tachometer count"""

# Bit shift values for multi-byte register operations
TACH_COUNT_HIGH_SHIFT = 8
"""Bit shift for high byte of tachometer count (bits 12-8)"""

TACH_COUNT_LOW_SHIFT = 3
"""Bit shift for low byte of tachometer count (3 LSBs are not used).
The TACH_READING_LOW register stores the count in bits 7:3, so we need
to shift right by 3 to get the actual count value."""

VALID_TACH_HIGH_SHIFT = 8
"""Bit shift for high byte of valid tachometer count"""

DRIVE_FAIL_LOW_SHIFT = 3
"""Bit shift for low byte of drive fail band count"""

DRIVE_FAIL_HIGH_SHIFT = 11
"""Bit shift for high byte of drive fail band count"""

DRIVE_FAIL_HIGH_MASK = 0x1F
"""Mask for high 5 bits of drive fail band count"""

# =============================================================================
# PID Gain Settings (REG_FANx_GAIN = 0x35 + offset)
# =============================================================================
# The GAIN register contains combined PID gain settings
# Format: [GP1:GP0 | GI2:GI1:GI0 | GD2:GD1:GD0]
# See datasheet pages 42-43 for detailed gain calculation

# Proportional gain (P) - bits 7-6
GAIN_P_MASK = 0xC0
GAIN_P_1X = 0x00
GAIN_P_2X = 0x40
GAIN_P_4X = 0x80
GAIN_P_8X = 0xC0

# Integral gain (I) - bits 5-3
GAIN_I_MASK = 0x38
GAIN_I_0X = 0x00
GAIN_I_1X = 0x08
GAIN_I_2X = 0x10
GAIN_I_4X = 0x18
GAIN_I_8X = 0x20
GAIN_I_16X = 0x28
GAIN_I_32X = 0x30

# Derivative gain (D) - bits 2-0
GAIN_D_MASK = 0x07
GAIN_D_0X = 0x00
GAIN_D_1X = 0x01
GAIN_D_2X = 0x02
GAIN_D_4X = 0x03
GAIN_D_8X = 0x04
GAIN_D_16X = 0x05
GAIN_D_32X = 0x06

# Default conservative PID gains: P=2x, I=1x, D=1x
DEFAULT_PID_GAIN = GAIN_P_2X | GAIN_I_1X | GAIN_D_1X

# =============================================================================
# Status Register Bit Masks
# =============================================================================

# Fan Status register bits (REG_FAN_STATUS = 0x24)
FAN_STATUS_FAN5 = 0x10
"""Fan 5 has a fault"""

FAN_STATUS_FAN4 = 0x08
"""Fan 4 has a fault"""

FAN_STATUS_FAN3 = 0x04
"""Fan 3 has a fault"""

FAN_STATUS_FAN2 = 0x02
"""Fan 2 has a fault"""

FAN_STATUS_FAN1 = 0x01
"""Fan 1 has a fault"""

FAN_STATUS_WATCH = 0x80
"""Watchdog timeout occurred"""

# Individual status register bits (REG_FAN_STALL_STATUS, etc.)
# Each register uses bits 4-0 for fans 5-1 respectively

# =============================================================================
# Timing Constants
# =============================================================================

INIT_DELAY_MS = 10
"""Initialization delay after reset (milliseconds)"""

WRITE_DELAY_MS = 1
"""Delay after write operations (milliseconds)"""

READ_DELAY_MS = 1
"""Delay after read operations (milliseconds)"""

WATCHDOG_TIMEOUT_SEC = 4
"""Watchdog timeout period (seconds)"""

SMBUS_TIMEOUT_MS = 30
"""SMBus timeout period (milliseconds) - can be disabled"""

# =============================================================================
# Default Configuration Values
# =============================================================================

DEFAULT_UPDATE_TIME = FAN_CONFIG1_UPDATE_200MS
"""Default fan control update time (200ms) - CRITICAL: 500ms breaks PWM control!"""

DEFAULT_EDGES = FAN_CONFIG1_EDGES_5
"""Default tachometer edges (5 edges = 2-pole fan)"""

DEFAULT_SPIN_UP_LEVEL = SPIN_UP_LEVEL_50_PERCENT
"""Default spin-up drive level (50%)"""

DEFAULT_MINIMUM_DRIVE = 51
"""Default minimum drive level (20% = 51/255)"""

DEFAULT_MAX_STEP = 31
"""Default maximum step size (valid range: 0-63 per hardware specification)"""

DEFAULT_PWM_FREQUENCY = PWM_FREQ_26000HZ
"""Default PWM base frequency (26 kHz)"""

# =============================================================================
# Temperature Limits (for future temperature sensing features)
# =============================================================================

MIN_TEMP_CELSIUS = -40
"""Minimum operating temperature"""

MAX_TEMP_CELSIUS = 125
"""Maximum operating temperature"""

# =============================================================================
# Error and Tolerance Values
# =============================================================================

RPM_TOLERANCE_PERCENT = 5
"""RPM measurement tolerance (±5%)"""

RPM_MEASUREMENT_ACCURACY_INTERNAL = 2.0
"""RPM accuracy with internal clock (±2%)"""

RPM_MEASUREMENT_ACCURACY_EXTERNAL = 0.5
"""RPM accuracy with external clock (±0.5%)"""
