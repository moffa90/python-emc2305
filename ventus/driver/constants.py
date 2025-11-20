"""
Hardware Constants

Register addresses, timing constants, and hardware-specific values.
"""

# I2C Bus Configuration
DEFAULT_I2C_BUS = 0
DEFAULT_I2C_LOCK_TIMEOUT = 5.0  # seconds
DEFAULT_I2C_LOCK_PATH = "/var/lock"

# Fan Controller I2C Addresses (examples - update based on actual hardware)
# DEVICE_1_ADDRESS = 0x2F
# DEVICE_2_ADDRESS = 0x4C
# DEVICE_3_ADDRESS = 0x4D

# Register Addresses (TBD - add based on actual chip datasheet)
# REG_CONFIG = 0x00
# REG_FAN_SPEED = 0x01
# REG_RPM_LOW = 0x02
# REG_RPM_HIGH = 0x03
# REG_TEMPERATURE = 0x04
# REG_STATUS = 0x05

# Timing Constants (TBD - adjust based on chip requirements)
INIT_DELAY_MS = 10
WRITE_DELAY_MS = 5
READ_DELAY_MS = 5

# Fan Speed Limits
MIN_FAN_SPEED = 0    # 0%
MAX_FAN_SPEED = 100  # 100%

# RPM Limits (example values - adjust based on actual fans)
MIN_RPM = 0
MAX_RPM = 10000

# Temperature Limits (example values)
MIN_TEMP = -40  # Celsius
MAX_TEMP = 125  # Celsius

# Status Flags (TBD - add based on chip datasheet)
# STATUS_FAN_FAULT = 0x01
# STATUS_TEMP_ALERT = 0x02
# STATUS_RPM_STALL = 0x04
