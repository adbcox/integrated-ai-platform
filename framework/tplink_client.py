"""TP-Link Deco mesh API client.

Uses the unofficial local Deco API (AES+RSA encrypted, documented at
https://github.com/AlexandrErohin/TP-Link-Deco-API).

Usage:
    from framework.tplink_client import DecoClient
    deco = DecoClient.from_env()
    print(deco.summary())

Env vars:
    DECO_HOST      IP of the primary Deco unit (usually 192.168.10.1 or a
                   dedicated mesh IP, e.g. 192.168.10.2)
    DECO_PASSWORD  Admin password (same as Deco app password)
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import struct
import time
import urllib.request
import urllib.error
from typing import Any


# AES-128-CBC helpers using Python stdlib (no cryptography package needed)
try:
    from Crypto.Cipher import AES  # pycryptodome if available
    from Crypto.Util.Padding import pad, unpad
    _HAS_CRYPTO = True
except ImportError:
    _HAS_CRYPTO = False


def _pkcs7_pad(data: bytes, block_size: int = 16) -> bytes:
    n = block_size - (len(data) % block_size)
    return data + bytes([n] * n)


def _pkcs7_unpad(data: bytes) -> bytes:
    return data[: -data[-1]]


def _aes_encrypt(key: bytes, iv: bytes, plaintext: bytes) -> bytes:
    if _HAS_CRYPTO:
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return cipher.encrypt(pad(plaintext, 16))
    # Pure-Python CBC (stdlib only, for when pycryptodome is absent)
    import ctypes
    raise RuntimeError(
        "pycryptodome required for Deco AES: pip install pycryptodome"
    )


def _aes_decrypt(key: bytes, iv: bytes, ciphertext: bytes) -> bytes:
    if _HAS_CRYPTO:
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return unpad(cipher.decrypt(ciphertext), 16)
    raise RuntimeError(
        "pycryptodome required for Deco AES: pip install pycryptodome"
    )


class DecoClient:
    """Low-level TP-Link Deco local API client."""

    _DEFAULT_KEY = b"RDpbLfCPsJZ7fiv"
    _DEFAULT_IV  = b"1234567890123456"

    def __init__(self, host: str, password: str, timeout: int = 10):
        self._host = host
        self._password = password
        self._timeout = timeout
        self._session_key: bytes | None = None
        self._session_iv: bytes | None = None
        self._stok: str = ""

    @classmethod
    def from_env(cls) -> "DecoClient":
        return cls(
            host=os.environ.get("DECO_HOST", "192.168.10.1"),
            password=os.environ.get("DECO_PASSWORD", ""),
        )

    # ── HTTP transport ────────────────────────────────────────────────────────

    def _post(self, path: str, body: dict) -> dict:
        url = f"http://{self._host}{path}"
        data = json.dumps(body).encode()
        req = urllib.request.Request(url, data=data, headers={
            "Content-Type": "application/json",
        }, method="POST")
        with urllib.request.urlopen(req, timeout=self._timeout) as resp:
            return json.loads(resp.read())

    # ── Auth ──────────────────────────────────────────────────────────────────

    def _login(self) -> None:
        if not _HAS_CRYPTO:
            raise RuntimeError("pycryptodome required: pip install pycryptodome")

        # Step 1: get RSA pubkey from device
        resp = self._post("/cgi-bin/luci/;stok=/login", {
            "method": "do",
            "login": {"username": "admin", "encrypt_type": "3"}
        })
        pubkey_n = int(resp["result"]["login"]["rsa_pubkey"]["n"], 16)
        pubkey_e = int(resp["result"]["login"]["rsa_pubkey"]["e"], 16)

        # Step 2: generate session key + iv, encrypt with RSA pubkey
        self._session_key = secrets.token_bytes(16)
        self._session_iv  = secrets.token_bytes(16)

        key_b64  = base64.b64encode(self._session_key).decode()
        iv_b64   = base64.b64encode(self._session_iv).decode()
        key_text = f"{key_b64}\r\n{iv_b64}\r\n"

        # Encrypt key_text with RSA (textbook RSA, not OAEP, as Deco uses)
        m = int(key_text.encode().hex(), 16)
        c = pow(m, pubkey_e, pubkey_n)
        enc_key = c.to_bytes((c.bit_length() + 7) // 8, "big").hex()

        # Step 3: encrypt password with default AES key and send
        pwd_enc = _aes_encrypt(
            self._DEFAULT_KEY, self._DEFAULT_IV,
            _pkcs7_pad(self._password.encode())
        )
        pwd_b64 = base64.b64encode(pwd_enc).decode()

        resp = self._post("/cgi-bin/luci/;stok=/login", {
            "method": "do",
            "login": {
                "username": "admin",
                "password": pwd_b64,
                "encrypt_type": "3",
                "key": enc_key,
            }
        })
        self._stok = resp["result"]["stok"]

    def _stok_or_login(self) -> str:
        if not self._stok:
            self._login()
        return self._stok

    def _api(self, params: dict) -> dict:
        stok = self._stok_or_login()
        return self._post(f"/cgi-bin/luci/;stok={stok}/admin/", params)

    # ── Device info ───────────────────────────────────────────────────────────

    def get_device_list(self) -> list[dict]:
        """All connected client devices."""
        resp = self._api({
            "method": "get",
            "device_list": {"name": ["default"]},
        })
        return resp.get("result", {}).get("device_list", [])

    def get_mesh_info(self) -> dict:
        """Deco unit topology (primary + satellites, signal strength)."""
        resp = self._api({
            "method": "get",
            "network": {"name": ["info"]},
        })
        return resp.get("result", {}).get("network", {})

    def get_internet_status(self) -> dict:
        """WAN/internet connection status."""
        resp = self._api({
            "method": "get",
            "internet": {"name": ["status"]},
        })
        return resp.get("result", {}).get("internet", {})

    def get_performance(self) -> dict:
        """CPU and memory utilization of the primary unit."""
        resp = self._api({
            "method": "get",
            "performance": {"name": ["cpu_usage", "mem_usage"]},
        })
        return resp.get("result", {}).get("performance", {})

    def get_connected_device_count(self) -> int:
        try:
            return len(self.get_device_list())
        except Exception:
            return -1

    # ── Convenience summary ───────────────────────────────────────────────────

    def summary(self) -> dict:
        result: dict[str, Any] = {"host": self._host}
        for key, fn in [
            ("mesh", self.get_mesh_info),
            ("internet", self.get_internet_status),
            ("devices", self.get_device_list),
            ("performance", self.get_performance),
        ]:
            try:
                result[key] = fn()
            except Exception as exc:
                result[key] = {"error": str(exc)}
        return result
