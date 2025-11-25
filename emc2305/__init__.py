"""
EMC2305 Fan Controller Driver

Python driver for the Microchip EMC2305 5-channel PWM fan controller.
Hardware-agnostic implementation supporting any platform with I2C.
"""

__version__ = "0.1.0"
__author__ = "Jose Luis Moffa"
__license__ = "MIT"

# Main driver classes
from emc2305.driver import EMC2305, FanController

# Exceptions
# Enums
# Data types and configuration
from emc2305.driver.emc2305 import (
    ControlMode,
    EMC2305CommunicationError,
    EMC2305ConfigurationError,
    EMC2305ConfigurationLockedError,
    EMC2305DeviceNotFoundError,
    EMC2305Error,
    EMC2305ValidationError,
    FanConfig,
    FanState,
    FanStatus,
    ProductFeatures,
)
from emc2305.driver.i2c import I2CBus, I2CError

# Configuration management
from emc2305.settings import (
    ConfigManager,
    EMC2305Config,
    FanChannelConfig,
    I2CConfig,
)

__all__ = [
    # Main classes
    "FanController",
    "EMC2305",
    "I2CBus",
    # Configuration management
    "ConfigManager",
    "I2CConfig",
    "EMC2305Config",
    "FanChannelConfig",
    # Data types
    "FanConfig",
    "FanState",
    "ProductFeatures",
    # Enums
    "ControlMode",
    "FanStatus",
    # Exceptions
    "EMC2305Error",
    "EMC2305DeviceNotFoundError",
    "EMC2305ConfigurationError",
    "EMC2305ConfigurationLockedError",
    "EMC2305CommunicationError",
    "EMC2305ValidationError",
    "I2CError",
    # Version
    "__version__",
]
