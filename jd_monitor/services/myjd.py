from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from myjdapi import Myjdapi

from jd_monitor.schemas import DeviceConfig, DeviceSnapshot, DownloadEntry, TransferTotals

logger = logging.getLogger("jd_monitor.myjd")


class MyJdError(Exception):
    def __init__(self, safe_message: str, debug_message: str | None = None) -> None:
        super().__init__(safe_message)
        self.safe_message = safe_message
        self.debug_message = debug_message or safe_message


class InvalidCredentialsError(MyJdError):
    pass


@dataclass
class PollState:
    previous_bytes: int = 0
    failure_streak: int = 0


class MyJDownloaderService:
    def __init__(self) -> None:
        self._api = Myjdapi()
        self._connected = False
        self._email = ""
        self._password = ""
        self._state: dict[str, PollState] = {}

    async def connect(self, email: str, password: str) -> None:
        if self._connected and email == self._email and password == self._password:
            return
        try:
            await asyncio.wait_for(asyncio.to_thread(self._api.connect, email, password), timeout=20)
        except Exception as exc:  # pragma: no cover - external library
            message = str(exc).upper()
            if "AUTH" in message or "LOGIN" in message:
                raise InvalidCredentialsError(
                    "Authentication with MyJDownloader failed.",
                    str(exc),
                ) from exc
            raise MyJdError(self._safe_error_message(exc), str(exc)) from exc
        self._connected = True
        self._email = email
        self._password = password

    async def fetch_snapshot(self, email: str, password: str, device: DeviceConfig) -> DeviceSnapshot:
        await self.connect(email, password)
        state = self._state.setdefault(device.id, PollState())
        try:
            jd_device = await asyncio.wait_for(asyncio.to_thread(self._api.get_device, device.name), timeout=15)
            links = await asyncio.wait_for(asyncio.to_thread(jd_device.downloads.query_links), timeout=20)
        except Exception as exc:  # pragma: no cover - external library
            text = str(exc).upper()
            if "TOKEN_INVALID" in text:
                self._connected = False
                await self.connect(email, password)
                return await self.fetch_snapshot(email, password, device)
            if "AUTH" in text or "LOGIN" in text:
                raise InvalidCredentialsError(
                    "Authentication with MyJDownloader failed.",
                    str(exc),
                ) from exc
            raise MyJdError(self._safe_error_message(exc), str(exc)) from exc

        totals = self._build_totals(links, state, device.poll_interval_seconds)
        recent = [
            DownloadEntry(
                name=item.get("name", "Unknown"),
                status=item.get("status", "UNKNOWN"),
                bytes_loaded=int(item.get("bytesLoaded", 0) or 0),
                bytes_total=int(item.get("bytesTotal", 0) or 0),
                eta_seconds=item.get("eta"),
            )
            for item in links[-5:]
        ]
        state.failure_streak = 0
        return DeviceSnapshot(
            device_id=device.id,
            device_name=device.name,
            display_name=device.display_name or device.name,
            status="online",
            message="Connected",
            platform=getattr(jd_device, "platform", None),
            version=getattr(jd_device, "version", None),
            uptime_seconds=getattr(jd_device, "uptime", None),
            disk_free_bytes=self._safe_int(getattr(jd_device, "diskSpace", None)),
            java_version=getattr(jd_device, "javaVersion", None),
            last_active_at=self._coerce_dt(getattr(jd_device, "lastActive", None)),
            connectivity_status="unknown" if device.connectivity.enabled else "unconfigured",
            connectivity_message=(
                "Local endpoint configured" if device.connectivity.enabled else "No local endpoint configured"
            ),
            totals=totals,
            recent_files=recent,
            checked_at=datetime.utcnow(),
            failure_streak=state.failure_streak,
        )

    @staticmethod
    def _coerce_dt(value: object) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, (int, float)):
            seconds = value / 1000 if value > 10_000_000_000 else value
            return datetime.fromtimestamp(seconds, tz=UTC).replace(tzinfo=None)
        return None

    @staticmethod
    def _safe_int(value: object) -> int | None:
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_error_message(exc: Exception) -> str:
        if isinstance(exc, UnicodeDecodeError):
            return "MyJDownloader returned unreadable device data."
        message = str(exc).upper()
        if "TOKEN_INVALID" in message:
            return "The MyJDownloader session expired and is being refreshed."
        if "TIMEOUT" in message:
            return "The device did not respond in time."
        if "DEVICE" in message and "NOT" in message and "FOUND" in message:
            return "The configured JDownloader device could not be found."
        return "The JDownloader device is currently unavailable."

    def _build_totals(self, links: list[dict], state: PollState, interval: int) -> TransferTotals:
        done_bytes = sum(int(item.get("bytesLoaded", 0) or 0) for item in links)
        total_bytes = sum(int(item.get("bytesTotal", 0) or 0) for item in links)
        speed = max(done_bytes - state.previous_bytes, 0) / max(interval, 1)
        state.previous_bytes = done_bytes
        return TransferTotals(
            active=sum(1 for item in links if item.get("status") == "DOWNLOADING"),
            waiting=sum(1 for item in links if item.get("status") == "WAITING"),
            finished=sum(1 for item in links if item.get("status") == "FINISHED"),
            paused=sum(1 for item in links if item.get("status") == "PAUSED"),
            errors=sum(1 for item in links if item.get("status") == "ERROR"),
            speed_bytes_per_second=speed,
            progress_percent=(done_bytes / total_bytes * 100) if total_bytes else 0.0,
            downloaded_bytes=done_bytes,
            total_bytes=total_bytes,
            links_total=len(links),
        )
