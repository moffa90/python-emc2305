"""
EMC2305 Hardware Driver

Low-level driver implementation for Microchip EMC2305 fan controller.
"""

from emc2305.driver.emc2305 import EMC2305

# Alias for backward compatibility and convenience
FanController = EMC2305

__all__ = ["EMC2305", "FanController"]
