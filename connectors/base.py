# Base connector class: Abstract interface for external service integration

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import os
import yaml


class BaseConnector(ABC):
    """
    Abstract base class for service connectors.

    Subclasses implement HTTP/RPC access to external systems.
    Handles authentication, retry policy, and error handling.
    """

    def __init__(self, connector_name: str = None, config: Dict[str, Any] = None):
        """
        Args:
            connector_name: Name of connector (loads from config/connectors.yaml if config is None)
            config: Connector configuration (optional, loads from YAML if not provided)
        """
        # Load config from YAML if not provided
        if config is None:
            config = self._load_config(connector_name or self.__class__.__name__)

        self.config = config
        self.timeout = config.get("timeout_seconds", 30)
        self.retry_policy = config.get("retry_policy", "exponential_backoff")

    @staticmethod
    def _load_config(connector_name: str) -> Dict[str, Any]:
        """Load connector config from config/connectors.yaml"""
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "config", "connectors.yaml"
        )
        if not os.path.exists(config_path):
            return {}

        with open(config_path) as f:
            connectors_config = yaml.safe_load(f) or {}
            return connectors_config.get("connectors", {}).get(connector_name, {})

    @abstractmethod
    def health_check(self) -> bool:
        """
        Verify connector can reach external service.

        Returns:
            True if service is reachable and responsive
        """
        pass

    @abstractmethod
    def execute(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an operation on the external service.

        Args:
            operation: Operation name (e.g., 'search', 'add_movie')
            params: Operation parameters

        Returns:
            Result dictionary
        """
        pass

    def _get_api_key(self, env_var: str) -> str:
        """
        Retrieve API key from environment.

        Args:
            env_var: Environment variable name

        Returns:
            API key value

        Raises:
            ValueError if environment variable not set
        """
        key = os.environ.get(env_var)
        if not key:
            raise ValueError(f"API key not found: {env_var}")
        return key

    def _validate_config(self, required_keys: list) -> None:
        """
        Validate required configuration keys are present.

        Args:
            required_keys: List of required config keys

        Raises:
            ValueError if required keys missing
        """
        missing = [k for k in required_keys if k not in self.config]
        if missing:
            raise ValueError(f"Missing config keys: {missing}")
