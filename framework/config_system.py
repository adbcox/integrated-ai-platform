"""Centralised YAML configuration with hot reload, encryption, and validation.

Environment selection::

    APP_ENV=production  → loads config/base.yaml then config/production.yaml
    APP_ENV=dev         → loads config/base.yaml then config/dev.yaml  (default)

Encrypted values::

    database.password: "ENC[base64ciphertext]"

To generate an encrypted value::

    from framework.config_system import get_config
    print(get_config().encrypt_value("my-secret"))
"""
from __future__ import annotations

import base64
import copy
import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, Callable, Optional

try:
    import yaml  # type: ignore[import]
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

try:
    from cryptography.fernet import Fernet, InvalidToken  # type: ignore[import]
    _CRYPTO_AVAILABLE = True
except ImportError:
    _CRYPTO_AVAILABLE = False

try:
    import jsonschema  # type: ignore[import]
    _JSONSCHEMA_AVAILABLE = True
except ImportError:
    _JSONSCHEMA_AVAILABLE = False

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_CONFIG_DIR = Path("config")
_BASE_FILE = _CONFIG_DIR / "base.yaml"
_SCHEMA_FILE = _CONFIG_DIR / "schema.json"
_ENC_PREFIX = "ENC["
_ENC_SUFFIX = "]"
_RELOAD_INTERVAL = 30.0  # seconds


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge *override* into *base*, returning a new dict.

    Args:
        base: The base dictionary.
        override: Values to overlay; scalars replace, dicts are merged recursively.

    Returns:
        New merged dictionary.
    """
    result = copy.deepcopy(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = copy.deepcopy(val)
    return result


def _get_nested(data: dict, dotted_key: str) -> Any:
    """Retrieve a value from *data* using a dot-notation key.

    Args:
        data: Nested dict to search.
        dotted_key: Key like "database.host".

    Returns:
        The value, or ``_MISSING`` sentinel if not found.
    """
    parts = dotted_key.split(".")
    node: Any = data
    for part in parts:
        if not isinstance(node, dict):
            return _MISSING
        node = node.get(part, _MISSING)
        if node is _MISSING:
            return _MISSING
    return node


def _set_nested(data: dict, dotted_key: str, value: Any) -> None:
    """Set a value in *data* using a dot-notation key, creating intermediate dicts.

    Args:
        data: Nested dict to mutate.
        dotted_key: Key like "database.host".
        value: Value to store.
    """
    parts = dotted_key.split(".")
    node = data
    for part in parts[:-1]:
        if part not in node or not isinstance(node[part], dict):
            node[part] = {}
        node = node[part]
    node[parts[-1]] = value


class _Missing:
    """Sentinel for missing config keys."""

    def __repr__(self) -> str:
        return "<MISSING>"


_MISSING = _Missing()


# ---------------------------------------------------------------------------
# ConfigManager
# ---------------------------------------------------------------------------

class ConfigManager:
    """Singleton configuration manager.

    Loads YAML files, supports dot-notation access, secret decryption,
    hot-reload, and JSON Schema validation.
    """

    _instance: Optional[ConfigManager] = None
    _instance_lock = threading.Lock()

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._raw_mtimes: dict[Path, float] = {}
        self._lock = threading.RLock()
        self._change_callbacks: list[Callable[[str, Any, Any], None]] = []
        self._fernet: Optional[Any] = None  # Fernet instance when available
        self._reload_timer: Optional[threading.Timer] = None
        self._env = os.environ.get("APP_ENV", "dev")
        self._load()
        self._start_reload_loop()

    # -- Singleton ------------------------------------------------------------

    @classmethod
    def instance(cls) -> ConfigManager:
        """Return the process-wide ConfigManager singleton.

        Returns:
            The singleton ConfigManager.
        """
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # -- Load & merge ---------------------------------------------------------

    def _load_yaml(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        if not _YAML_AVAILABLE:
            logger.warning("ConfigManager: PyYAML not installed; cannot load %s", path)
            return {}
        try:
            with path.open("r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh) or {}
            if not isinstance(data, dict):
                logger.warning("ConfigManager: %s root is not a dict", path)
                return {}
            return data
        except Exception as exc:
            logger.error("ConfigManager: failed to load %s: %s", path, exc)
            return {}

    def _load(self) -> None:
        """(Re-)load configuration from disk into memory."""
        base = self._load_yaml(_BASE_FILE)
        env_file = _CONFIG_DIR / f"{self._env}.yaml"
        env_data = self._load_yaml(env_file)
        merged = _deep_merge(base, env_data)
        self._validate(merged)
        with self._lock:
            self._data = merged
        # Track mtimes for hot-reload
        for path in (_BASE_FILE, env_file):
            if path.exists():
                self._raw_mtimes[path] = path.stat().st_mtime
        self._init_fernet()

    def _init_fernet(self) -> None:
        if not _CRYPTO_AVAILABLE:
            return
        secret_key_b64 = os.environ.get("CONFIG_SECRET_KEY", "")
        if not secret_key_b64:
            return
        try:
            key_bytes = base64.b64decode(secret_key_b64)
            # Fernet requires a URL-safe base64-encoded 32-byte key
            self._fernet = Fernet(base64.urlsafe_b64encode(key_bytes[:32]))
        except Exception as exc:
            logger.warning("ConfigManager: could not initialise Fernet: %s", exc)

    def _validate(self, data: dict[str, Any]) -> None:
        if not _JSONSCHEMA_AVAILABLE:
            return
        if not _SCHEMA_FILE.exists():
            return
        try:
            with _SCHEMA_FILE.open("r", encoding="utf-8") as fh:
                schema = json.load(fh)
            jsonschema.validate(instance=data, schema=schema)
            logger.debug("ConfigManager: schema validation passed")
        except Exception as exc:
            logger.warning("ConfigManager: schema validation failed: %s", exc)

    # -- Hot reload -----------------------------------------------------------

    def _start_reload_loop(self) -> None:
        self._reload_timer = threading.Timer(_RELOAD_INTERVAL, self._reload_tick)
        self._reload_timer.daemon = True
        self._reload_timer.start()

    def _reload_tick(self) -> None:
        try:
            self._check_and_reload()
        except Exception as exc:
            logger.warning("ConfigManager: reload tick error: %s", exc)
        finally:
            self._start_reload_loop()

    def _check_and_reload(self) -> None:
        env_file = _CONFIG_DIR / f"{self._env}.yaml"
        changed = False
        for path in (_BASE_FILE, env_file):
            if not path.exists():
                continue
            mtime = path.stat().st_mtime
            if mtime != self._raw_mtimes.get(path, 0.0):
                changed = True
                break
        if not changed:
            return
        logger.info("ConfigManager: config files changed, reloading")
        with self._lock:
            old_data = copy.deepcopy(self._data)
        self._load()
        with self._lock:
            new_data = copy.deepcopy(self._data)
        self._fire_callbacks(old_data, new_data)

    def _fire_callbacks(self, old: dict, new: dict) -> None:
        all_keys = set(_flatten_keys(old)) | set(_flatten_keys(new))
        for key in all_keys:
            old_val = _get_nested(old, key)
            new_val = _get_nested(new, key)
            if old_val != new_val:
                for cb in self._change_callbacks:
                    try:
                        cb(key, old_val, new_val)
                    except Exception as exc:
                        logger.warning("ConfigManager: change callback error: %s", exc)

    # -- Public API -----------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a config value by dot-notation key.

        Args:
            key: Dot-separated key, e.g. ``"database.host"``.
            default: Returned when the key is absent.

        Returns:
            The config value, decrypted if prefixed with ``ENC[``.
        """
        with self._lock:
            val = _get_nested(self._data, key)
        if isinstance(val, _Missing):
            return default
        if isinstance(val, str) and val.startswith(_ENC_PREFIX):
            return self.decrypt_value(val)
        return val

    def set(self, key: str, value: Any) -> None:
        """Update a config value in-memory (not persisted).

        Args:
            key: Dot-separated key.
            value: New value.
        """
        with self._lock:
            old = _get_nested(self._data, key)
            _set_nested(self._data, key, value)
        for cb in self._change_callbacks:
            try:
                cb(key, old if not isinstance(old, _Missing) else None, value)
            except Exception as exc:
                logger.warning("ConfigManager: change callback error: %s", exc)

    def save(self, path: Optional[Path] = None) -> None:
        """Persist the current in-memory config to a YAML file.

        Args:
            path: Destination path; defaults to the env-specific file.
        """
        if not _YAML_AVAILABLE:
            logger.error("ConfigManager: PyYAML not available; cannot save")
            return
        target = path or (_CONFIG_DIR / f"{self._env}.yaml")
        target.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            data = copy.deepcopy(self._data)
        try:
            with target.open("w", encoding="utf-8") as fh:
                yaml.dump(data, fh, default_flow_style=False, allow_unicode=True)
            logger.info("ConfigManager: config saved to %s", target)
        except OSError as exc:
            logger.error("ConfigManager: failed to save: %s", exc)

    def register_change_callback(
        self,
        callback: Callable[[str, Any, Any], None],
    ) -> None:
        """Register a callback invoked when any config value changes.

        Args:
            callback: ``callback(key, old_value, new_value)`` — called per
                changed key on reload.
        """
        self._change_callbacks.append(callback)

    # -- Encryption -----------------------------------------------------------

    def encrypt_value(self, plaintext: str) -> str:
        """Encrypt a plaintext string for storage in config.

        Args:
            plaintext: The secret value to encrypt.

        Returns:
            String in the form ``ENC[base64ciphertext]``.

        Raises:
            RuntimeError: If Fernet is not initialised.
        """
        if self._fernet is None:
            raise RuntimeError(
                "ConfigManager: CONFIG_SECRET_KEY not set or cryptography not installed"
            )
        token = self._fernet.encrypt(plaintext.encode("utf-8"))
        return f"{_ENC_PREFIX}{token.decode('ascii')}{_ENC_SUFFIX}"

    def decrypt_value(self, enc_str: str) -> str:
        """Decrypt an ``ENC[...]`` value.

        Args:
            enc_str: Encrypted string in ``ENC[...]`` form.

        Returns:
            Decrypted plaintext.

        Raises:
            RuntimeError: If Fernet is not initialised.
            ValueError: If the token is invalid or corrupted.
        """
        if self._fernet is None:
            raise RuntimeError(
                "ConfigManager: CONFIG_SECRET_KEY not set or cryptography not installed"
            )
        if not (enc_str.startswith(_ENC_PREFIX) and enc_str.endswith(_ENC_SUFFIX)):
            raise ValueError(f"ConfigManager: not an encrypted value: {enc_str!r}")
        inner = enc_str[len(_ENC_PREFIX):-len(_ENC_SUFFIX)]
        try:
            return self._fernet.decrypt(inner.encode("ascii")).decode("utf-8")
        except Exception as exc:
            raise ValueError(f"ConfigManager: decryption failed: {exc}") from exc

    def as_dict(self) -> dict[str, Any]:
        """Return a deep copy of the full config dict.

        Returns:
            Nested dict of all config values.
        """
        with self._lock:
            return copy.deepcopy(self._data)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _flatten_keys(data: dict, prefix: str = "") -> list[str]:
    """Yield all dot-notation keys from a nested dict.

    Args:
        data: Nested dict.
        prefix: Accumulated prefix (used in recursion).

    Returns:
        List of dot-separated key strings.
    """
    keys: list[str] = []
    for k, v in data.items():
        full_key = f"{prefix}.{k}" if prefix else k
        keys.append(full_key)
        if isinstance(v, dict):
            keys.extend(_flatten_keys(v, full_key))
    return keys


# ---------------------------------------------------------------------------
# Module-level helper
# ---------------------------------------------------------------------------

def get_config() -> ConfigManager:
    """Return the process-wide ConfigManager singleton.

    Returns:
        Singleton ConfigManager instance.
    """
    return ConfigManager.instance()
