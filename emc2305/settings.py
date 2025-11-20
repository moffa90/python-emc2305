# Copyright (c) 2025 Contributors to the microchip-emc2305 project
# SPDX-License-Identifier: MIT

"""
Configuration Management

Handles loading and saving configuration for EMC2305 fan controller.
"""

import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum

try:
    import yaml
except ImportError:
    yaml = None

from emc2305.driver import constants as const

logger = logging.getLogger(__name__)


class ControlMode(Enum):
    """Fan control mode."""
    PWM = "pwm"  # Direct PWM control (0-100%)
    FSC = "fsc"  # Fan Speed Control (closed-loop RPM control)


@dataclass
class I2CConfig:
    """I2C bus configuration."""
    bus: int = const.DEFAULT_I2C_BUS
    lock_enabled: bool = True
    lock_timeout: float = const.DEFAULT_I2C_LOCK_TIMEOUT
    lock_path: str = const.DEFAULT_I2C_LOCK_PATH


@dataclass
class FanChannelConfig:
    """Configuration for a single fan channel."""
    name: str = "Fan"
    enabled: bool = True
    control_mode: str = "pwm"  # "pwm" or "fsc"

    # RPM limits (for FSC mode)
    min_rpm: int = const.MIN_RPM
    max_rpm: int = const.MAX_RPM
    default_target_rpm: int = 2000

    # PWM limits (for PWM mode)
    min_duty_percent: int = 20
    max_duty_percent: int = 100
    default_duty_percent: int = 50

    # Advanced settings
    update_time_ms: int = 500  # Control loop update time (100/200/300/400/500/800/1200/1600)
    edges: int = 5  # Tachometer edges (3/5/7/9 for 1/2/3/4-pole fans)
    max_step: int = const.DEFAULT_MAX_STEP  # Maximum PWM change per update

    # PWM frequency control
    pwm_divide: int = const.DEFAULT_PWM_DIVIDE  # PWM frequency divider (1, 2, 4, 8, 16, 32)

    # Spin-up configuration
    spin_up_level_percent: int = 50  # Drive level during spin-up (30/35/40/45/50/55/60/65)
    spin_up_time_ms: int = 500  # Spin-up duration (0-1550 in 50ms increments)

    # PID gains (for FSC mode)
    pid_gain_p: int = 2  # Proportional gain (1/2/4/8)
    pid_gain_i: int = 1  # Integral gain (0/1/2/4/8/16/32)
    pid_gain_d: int = 1  # Derivative gain (0/1/2/4/8/16/32)


@dataclass
class EMC2305Config:
    """EMC2305 device configuration."""
    name: str = "EMC2305 Fan Controller"
    address: int = const.DEFAULT_DEVICE_ADDRESS
    enabled: bool = True

    # Clock configuration
    use_external_clock: bool = False  # Use external 32.768kHz crystal

    # PWM configuration
    pwm_frequency_hz: int = 26000  # Base PWM frequency (26000/19531/4882/2441)
    pwm_polarity_inverted: bool = False  # Invert PWM polarity
    pwm_output_push_pull: bool = False  # Use push-pull output (default: open-drain)

    # Safety features
    enable_watchdog: bool = False  # Enable 4-second watchdog timer
    enable_alerts: bool = True  # Enable ALERT# pin for fault notification

    # Fan channel configurations
    fans: Dict[int, FanChannelConfig] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize default fan configurations if not provided."""
        if not self.fans:
            for channel in range(1, const.NUM_FAN_CHANNELS + 1):
                self.fans[channel] = FanChannelConfig(
                    name=f"Fan {channel}"
                )


@dataclass
class DriverConfig:
    """Main driver configuration."""
    i2c: I2CConfig = field(default_factory=I2CConfig)
    emc2305: EMC2305Config = field(default_factory=EMC2305Config)

    # Global settings
    log_level: str = "INFO"
    log_file: Optional[str] = None  # Log to file (None = console only)


class ConfigManager:
    """
    Configuration file manager.

    Handles loading, saving, and validation of configuration files.
    Supports YAML format and provides sensible defaults.
    """

    DEFAULT_CONFIG_LOCATIONS = [
        Path.home() / ".config" / "emc2305" / "emc2305.yaml",
        Path("/etc/emc2305/emc2305.yaml"),
    ]

    def __init__(self, config_path: Optional[Path] = None) -> None:
        """
        Initialize configuration manager.

        Args:
            config_path: Optional path to configuration file.
                        If not provided, searches default locations.
        """
        if yaml is None:
            logger.warning("PyYAML not installed, configuration loading disabled")

        self.config_path = config_path
        if self.config_path is None:
            self.config_path = self._find_config()

        self.config = DriverConfig()

    def _find_config(self) -> Optional[Path]:
        """Find configuration file in default locations."""
        for path in self.DEFAULT_CONFIG_LOCATIONS:
            if path.exists():
                logger.info(f"Found configuration: {path}")
                return path
        return None

    def load(self) -> DriverConfig:
        """
        Load configuration from file.

        Returns:
            DriverConfig with loaded values or defaults
        """
        if self.config_path is None or not self.config_path.exists():
            logger.info("No configuration file found, using defaults")
            return self.config

        if yaml is None:
            logger.warning("PyYAML not installed, cannot load configuration")
            return self.config

        try:
            with open(self.config_path, "r") as f:
                data = yaml.safe_load(f)

            if data is None:
                return self.config

            # Load I2C configuration
            if "i2c" in data:
                i2c_data = data["i2c"]
                self.config.i2c = I2CConfig(
                    bus=i2c_data.get("bus", const.DEFAULT_I2C_BUS),
                    lock_enabled=i2c_data.get("lock_enabled", True),
                    lock_timeout=i2c_data.get("lock_timeout", const.DEFAULT_I2C_LOCK_TIMEOUT),
                    lock_path=i2c_data.get("lock_path", const.DEFAULT_I2C_LOCK_PATH),
                )

            # Load EMC2305 configuration
            if "emc2305" in data:
                emc_data = data["emc2305"]

                # Parse address (support hex strings like "0x61")
                address = emc_data.get("address", const.DEFAULT_DEVICE_ADDRESS)
                if isinstance(address, str):
                    address = int(address, 16)

                # Load fan channel configurations
                fans = {}
                if "fans" in emc_data:
                    for channel_str, fan_data in emc_data["fans"].items():
                        channel = int(channel_str) if isinstance(channel_str, str) else channel_str
                        fans[channel] = FanChannelConfig(
                            name=fan_data.get("name", f"Fan {channel}"),
                            enabled=fan_data.get("enabled", True),
                            control_mode=fan_data.get("control_mode", "pwm"),
                            min_rpm=fan_data.get("min_rpm", const.MIN_RPM),
                            max_rpm=fan_data.get("max_rpm", const.MAX_RPM),
                            default_target_rpm=fan_data.get("default_target_rpm", 2000),
                            min_duty_percent=fan_data.get("min_duty_percent", 20),
                            max_duty_percent=fan_data.get("max_duty_percent", 100),
                            default_duty_percent=fan_data.get("default_duty_percent", 50),
                            update_time_ms=fan_data.get("update_time_ms", 500),
                            edges=fan_data.get("edges", 5),
                            max_step=fan_data.get("max_step", const.DEFAULT_MAX_STEP),
                            pwm_divide=fan_data.get("pwm_divide", const.DEFAULT_PWM_DIVIDE),
                            spin_up_level_percent=fan_data.get("spin_up_level_percent", 50),
                            spin_up_time_ms=fan_data.get("spin_up_time_ms", 500),
                            pid_gain_p=fan_data.get("pid_gain_p", 2),
                            pid_gain_i=fan_data.get("pid_gain_i", 1),
                            pid_gain_d=fan_data.get("pid_gain_d", 1),
                        )

                self.config.emc2305 = EMC2305Config(
                    name=emc_data.get("name", "EMC2305 Fan Controller"),
                    address=address,
                    enabled=emc_data.get("enabled", True),
                    use_external_clock=emc_data.get("use_external_clock", False),
                    pwm_frequency_hz=emc_data.get("pwm_frequency_hz", 26000),
                    pwm_polarity_inverted=emc_data.get("pwm_polarity_inverted", False),
                    pwm_output_push_pull=emc_data.get("pwm_output_push_pull", False),
                    enable_watchdog=emc_data.get("enable_watchdog", False),
                    enable_alerts=emc_data.get("enable_alerts", True),
                    fans=fans,
                )

                # Initialize missing fan channels with defaults
                for channel in range(1, const.NUM_FAN_CHANNELS + 1):
                    if channel not in self.config.emc2305.fans:
                        self.config.emc2305.fans[channel] = FanChannelConfig(
                            name=f"Fan {channel}"
                        )

            # Load global settings
            self.config.log_level = data.get("log_level", "INFO")
            self.config.log_file = data.get("log_file")

            logger.info(f"Configuration loaded from {self.config_path}")
            return self.config

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return self.config

    def save(self, config: DriverConfig) -> bool:
        """
        Save configuration to file.

        Args:
            config: Configuration to save

        Returns:
            True if saved successfully, False otherwise
        """
        if yaml is None:
            logger.warning("PyYAML not installed, cannot save configuration")
            return False

        if self.config_path is None:
            self.config_path = self.DEFAULT_CONFIG_LOCATIONS[0]

        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Convert config to dictionary
            data = {
                "i2c": {
                    "bus": config.i2c.bus,
                    "lock_enabled": config.i2c.lock_enabled,
                    "lock_timeout": config.i2c.lock_timeout,
                    "lock_path": config.i2c.lock_path,
                },
                "emc2305": {
                    "name": config.emc2305.name,
                    "address": f"0x{config.emc2305.address:02X}",
                    "enabled": config.emc2305.enabled,
                    "use_external_clock": config.emc2305.use_external_clock,
                    "pwm_frequency_hz": config.emc2305.pwm_frequency_hz,
                    "pwm_polarity_inverted": config.emc2305.pwm_polarity_inverted,
                    "pwm_output_push_pull": config.emc2305.pwm_output_push_pull,
                    "enable_watchdog": config.emc2305.enable_watchdog,
                    "enable_alerts": config.emc2305.enable_alerts,
                    "fans": {
                        channel: {
                            "name": fan.name,
                            "enabled": fan.enabled,
                            "control_mode": fan.control_mode,
                            "min_rpm": fan.min_rpm,
                            "max_rpm": fan.max_rpm,
                            "default_target_rpm": fan.default_target_rpm,
                            "min_duty_percent": fan.min_duty_percent,
                            "max_duty_percent": fan.max_duty_percent,
                            "default_duty_percent": fan.default_duty_percent,
                            "update_time_ms": fan.update_time_ms,
                            "edges": fan.edges,
                            "max_step": fan.max_step,
                            "pwm_divide": fan.pwm_divide,
                            "spin_up_level_percent": fan.spin_up_level_percent,
                            "spin_up_time_ms": fan.spin_up_time_ms,
                            "pid_gain_p": fan.pid_gain_p,
                            "pid_gain_i": fan.pid_gain_i,
                            "pid_gain_d": fan.pid_gain_d,
                        }
                        for channel, fan in config.emc2305.fans.items()
                    },
                },
                "log_level": config.log_level,
            }

            if config.log_file:
                data["log_file"] = config.log_file

            with open(self.config_path, "w") as f:
                yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

            logger.info(f"Configuration saved to {self.config_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False

    def create_default(self, path: Optional[Path] = None) -> bool:
        """
        Create default configuration file.

        Args:
            path: Optional path for config file (default: user config location)

        Returns:
            True if created successfully, False otherwise
        """
        if path:
            self.config_path = path
        elif self.config_path is None:
            self.config_path = self.DEFAULT_CONFIG_LOCATIONS[0]

        # Create default configuration
        default_config = DriverConfig()

        # Configure all 5 fan channels with sensible defaults
        default_config.emc2305.fans = {
            1: FanChannelConfig(
                name="CPU Fan",
                control_mode="fsc",
                default_target_rpm=3000,
                min_rpm=1000,
                max_rpm=4500,
            ),
            2: FanChannelConfig(
                name="Case Fan 1",
                control_mode="pwm",
                default_duty_percent=40,
                min_duty_percent=30,
            ),
            3: FanChannelConfig(
                name="Case Fan 2",
                control_mode="pwm",
                default_duty_percent=40,
                min_duty_percent=30,
            ),
            4: FanChannelConfig(
                name="Exhaust Fan",
                control_mode="pwm",
                default_duty_percent=50,
                min_duty_percent=30,
            ),
            5: FanChannelConfig(
                name="Spare Fan",
                enabled=False,
                control_mode="pwm",
                default_duty_percent=0,
            ),
        }

        return self.save(default_config)
