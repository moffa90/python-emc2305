"""
Cellgain Ventus - I2C Fan Controller System

A professional fan control system for embedded Linux platforms.
"""

__version__ = "0.1.0"
__author__ = "Cellgain"
__email__ = "contact@cellgain.com"

from ventus.driver import FanController

__all__ = ["FanController", "__version__"]
