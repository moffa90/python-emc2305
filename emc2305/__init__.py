"""
EMC2305 Fan Controller Driver

Python driver for the Microchip EMC2305 5-channel PWM fan controller.
Hardware-agnostic implementation supporting any platform with I2C.
"""

__version__ = "0.1.0"
__author__ = "Contributors to the microchip-emc2305 project"
__license__ = "MIT"

from emc2305.driver import FanController

__all__ = ["FanController", "__version__"]
