"""Hardware device adapter pattern for peripheral integration.

Use this pattern when wrapping a hardware device (printer, scanner, sensor,
serial/Bluetooth/USB device) behind a clean Python interface.

Key ideas:
  - Abstract base defines the contract; concrete class wraps the hardware
  - __enter__/__exit__ manage device lifecycle (open/close connection)
  - Distinguish connection errors (retry) from protocol errors (fail fast)
  - Keep the hardware-speak in ONE class; callers only see domain methods

When to use:
  - Niimbot/ZPL label printers over Bluetooth or USB
  - Serial port devices (barcode scanners, scales, receipt printers)
  - GPIO/I2C/SPI sensors on embedded boards
  - Any device with open/send/close lifecycle
"""
from __future__ import annotations

import abc
import time
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


# ── Domain types ─────────────────────────────────────────────────────────────

@dataclass
class PrintJob:
    text: str
    copies: int = 1
    density: int = 5  # 1-10 scale


@dataclass
class DeviceStatus:
    connected: bool
    battery_pct: Optional[int] = None
    error: Optional[str] = None


# ── Abstract base ─────────────────────────────────────────────────────────────

class PrinterAdapter(abc.ABC):
    """Contract for all label printer backends."""

    @abc.abstractmethod
    def connect(self) -> None: ...

    @abc.abstractmethod
    def disconnect(self) -> None: ...

    @abc.abstractmethod
    def print_label(self, job: PrintJob) -> bool: ...

    @abc.abstractmethod
    def status(self) -> DeviceStatus: ...

    def __enter__(self) -> "PrinterAdapter":
        self.connect()
        return self

    def __exit__(self, *_) -> None:
        self.disconnect()


# ── Concrete implementation ───────────────────────────────────────────────────

class NiimbotBluetoothAdapter(PrinterAdapter):
    """Wraps Niimbot B1/B21/D11 over Bluetooth RFCOMM."""

    def __init__(self, mac_address: str, channel: int = 1) -> None:
        self.mac = mac_address
        self.channel = channel
        self._sock = None

    def connect(self) -> None:
        # Real implementation: import bluetooth; self._sock = bluetooth.BluetoothSocket(...)
        logger.info("Connecting to %s ch%d", self.mac, self.channel)
        self._sock = object()  # placeholder

    def disconnect(self) -> None:
        if self._sock:
            logger.info("Disconnecting from %s", self.mac)
            self._sock = None

    def print_label(self, job: PrintJob) -> bool:
        if not self._sock:
            raise RuntimeError("Not connected")
        # Real: encode job to Niimbot packet format and send via self._sock
        logger.info("Printing %r (×%d)", job.text, job.copies)
        return True

    def status(self) -> DeviceStatus:
        if not self._sock:
            return DeviceStatus(connected=False, error="No connection")
        return DeviceStatus(connected=True, battery_pct=80)


# ── Retry wrapper ─────────────────────────────────────────────────────────────

class RetryingPrinterAdapter(PrinterAdapter):
    """Decorator that retries print_label on transient failures."""

    def __init__(self, inner: PrinterAdapter, max_attempts: int = 3) -> None:
        self._inner = inner
        self._max = max_attempts

    def connect(self) -> None:
        self._inner.connect()

    def disconnect(self) -> None:
        self._inner.disconnect()

    def print_label(self, job: PrintJob) -> bool:
        for attempt in range(1, self._max + 1):
            try:
                return self._inner.print_label(job)
            except Exception as exc:
                if attempt == self._max:
                    raise
                logger.warning("Print attempt %d failed: %s — retrying", attempt, exc)
                time.sleep(1)
        return False

    def status(self) -> DeviceStatus:
        return self._inner.status()


# ── Usage example ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    adapter = RetryingPrinterAdapter(
        NiimbotBluetoothAdapter(mac_address="AA:BB:CC:DD:EE:FF"),
        max_attempts=3,
    )

    with adapter:
        st = adapter.status()
        print(f"Battery: {st.battery_pct}%")
        ok = adapter.print_label(PrintJob(text="Order #1234", copies=2))
        print("Printed:", ok)
