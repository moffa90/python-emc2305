"""
Configuration Management

Handles loading and saving configuration for Ventus fan controller.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import yaml
except ImportError:
    yaml = None

logger = logging.getLogger(__name__)


@dataclass
class I2CConfig:
    """I2C bus configuration."""
    bus: int = 0
    lock_enabled: bool = True
    lock_timeout: float = 5.0
    lock_path: str = "/var/lock"


@dataclass
class DeviceConfig:
    """Individual fan controller device configuration."""
    name: str = "Fan Controller"
    address: int = 0x2F
    enabled: bool = True
    min_speed: int = 0
    max_speed: int = 100
    default_speed: int = 50


@dataclass
class VentusConfig:
    """Main Ventus configuration."""
    i2c: I2CConfig = field(default_factory=I2CConfig)
    devices: Dict[str, DeviceConfig] = field(default_factory=dict)

    # Global defaults
    log_level: str = "INFO"
    auto_start: bool = False


class ConfigManager:
    """
    Configuration file manager.

    Handles loading, saving, and validation of configuration files.
    Supports YAML format (default) and provides sensible defaults.
    """

    DEFAULT_CONFIG_LOCATIONS = [
        Path.home() / ".config" / "ventus" / "ventus.yaml",
        Path("/etc/ventus/ventus.yaml"),
    ]

    def __init__(self, config_path: Optional[Path] = None):
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

        self.config = VentusConfig()

    def _find_config(self) -> Optional[Path]:
        """Find configuration file in default locations."""
        for path in self.DEFAULT_CONFIG_LOCATIONS:
            if path.exists():
                logger.info(f"Found configuration: {path}")
                return path
        return None

    def load(self) -> VentusConfig:
        """
        Load configuration from file.

        Returns:
            VentusConfig with loaded values or defaults
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
                    bus=i2c_data.get("bus", 0),
                    lock_enabled=i2c_data.get("lock_enabled", True),
                    lock_timeout=i2c_data.get("lock_timeout", 5.0),
                    lock_path=i2c_data.get("lock_path", "/var/lock"),
                )

            # Load device configurations
            if "devices" in data:
                for name, dev_data in data["devices"].items():
                    self.config.devices[name] = DeviceConfig(
                        name=dev_data.get("name", name),
                        address=int(dev_data.get("address", 0x2F), 16) if isinstance(dev_data.get("address"), str) else dev_data.get("address", 0x2F),
                        enabled=dev_data.get("enabled", True),
                        min_speed=dev_data.get("min_speed", 0),
                        max_speed=dev_data.get("max_speed", 100),
                        default_speed=dev_data.get("default_speed", 50),
                    )

            # Load global settings
            self.config.log_level = data.get("log_level", "INFO")
            self.config.auto_start = data.get("auto_start", False)

            logger.info(f"Configuration loaded from {self.config_path}")
            return self.config

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return self.config

    def save(self, config: VentusConfig) -> bool:
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
                "devices": {
                    name: {
                        "name": dev.name,
                        "address": f"0x{dev.address:02X}",
                        "enabled": dev.enabled,
                        "min_speed": dev.min_speed,
                        "max_speed": dev.max_speed,
                        "default_speed": dev.default_speed,
                    }
                    for name, dev in config.devices.items()
                },
                "log_level": config.log_level,
                "auto_start": config.auto_start,
            }

            with open(self.config_path, "w") as f:
                yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

            logger.info(f"Configuration saved to {self.config_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False

    def create_default(self) -> bool:
        """
        Create default configuration file.

        Returns:
            True if created successfully, False otherwise
        """
        default_config = VentusConfig()

        # Add example device
        default_config.devices["fan1"] = DeviceConfig(
            name="Fan 1",
            address=0x2F,
            enabled=True,
            min_speed=0,
            max_speed=100,
            default_speed=50,
        )

        return self.save(default_config)
