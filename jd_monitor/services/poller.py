from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

from jd_monitor.repo_utils import ConfigRepository, DeviceStateRepository, NotificationRepository
from jd_monitor.schemas import AppConfig, DeviceConfig, DeviceSnapshot, HealthStatus, TransferTotals
from jd_monitor.services.events import classify_event
from jd_monitor.services.myjd import InvalidCredentialsError, MyJdError, MyJDownloaderService
from jd_monitor.services.notifications import NotificationService

logger = logging.getLogger("jd_monitor.poller")


class PollerService:
    def __init__(
        self,
        config_repo: ConfigRepository,
        device_repo: DeviceStateRepository,
        notification_repo: NotificationRepository,
        myjd_service: MyJDownloaderService,
        notification_service: NotificationService,
    ) -> None:
        self.config_repo = config_repo
        self.device_repo = device_repo
        self.notification_repo = notification_repo
        self.myjd_service = myjd_service
        self.notification_service = notification_service
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()
        self._next_due: dict[str, datetime] = {}
        self.health = HealthStatus(status="degraded", message="Starting background poller")

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._stop.clear()
        self._task = asyncio.create_task(self._run(), name="jd-monitor-poller")

    async def stop(self) -> None:
        self._stop.set()
        if self._task:
            await self._task

    async def trigger_now(self) -> None:
        for snapshot in self.device_repo.list():
            self._next_due[snapshot.device_id] = datetime.utcnow()

    async def _run(self) -> None:
        while not self._stop.is_set():
            config = self.config_repo.load()
            if config is None:
                self.health = HealthStatus(status="degraded", message="Waiting for configuration")
                await asyncio.sleep(2)
                continue
            await self._poll_cycle(config)
            await asyncio.sleep(2)

    async def _poll_cycle(self, config: AppConfig) -> None:
        tasks = []
        now = datetime.utcnow()
        for device in config.devices:
            if not device.enabled:
                continue
            due = self._next_due.get(device.id, now)
            if now >= due:
                tasks.append(self._poll_device(config, device))
        if tasks:
            await asyncio.gather(*tasks)

    async def _poll_device(self, config: AppConfig, device: DeviceConfig) -> None:
        previous = self.device_repo.get(device.id)
        try:
            snapshot = await self.myjd_service.fetch_snapshot(
                config.credentials.email,
                config.credentials.password,
                device,
            )
            self.health = HealthStatus(status="ok", message="Polling normally")
            backoff_seconds = device.poll_interval_seconds
        except InvalidCredentialsError as exc:
            snapshot = self._offline_snapshot(device, "invalid_credentials", str(exc), previous)
            self.health = HealthStatus(status="error", message="Invalid MyJDownloader credentials")
            logger.warning(
                "MyJDownloader authentication failed",
                extra={"extra": {"device_id": device.id, "error": exc.debug_message}},
            )
            backoff_seconds = min(device.poll_interval_seconds * 2, 900)
        except MyJdError as exc:
            snapshot = self._offline_snapshot(device, "offline", str(exc), previous)
            self.health = HealthStatus(status="degraded", message="MyJDownloader connectivity issues")
            logger.warning(
                "MyJDownloader device poll failed",
                extra={"extra": {"device_id": device.id, "error": exc.debug_message}},
            )
            backoff_seconds = min(device.poll_interval_seconds * 2, 900)

        self.device_repo.save(snapshot)
        self._next_due[device.id] = datetime.utcnow() + timedelta(seconds=backoff_seconds)
        event_type = classify_event(previous, snapshot)

        for webhook in config.webhooks:
            if not webhook.enabled or webhook.id not in device.webhook_ids or device.id not in webhook.device_ids:
                continue
            if event_type not in webhook.notification_modes:
                continue
            await self.notification_service.send(webhook, snapshot, event_type)

    @staticmethod
    def _offline_snapshot(
        device: DeviceConfig,
        status: str,
        message: str,
        previous: DeviceSnapshot | None,
    ) -> DeviceSnapshot:
        failure_streak = (previous.failure_streak if previous else 0) + 1
        return DeviceSnapshot(
            device_id=device.id,
            device_name=device.name,
            display_name=device.display_name or device.name,
            status=status,  # type: ignore[arg-type]
            message=message,
            platform=previous.platform if previous else None,
            version=previous.version if previous else None,
            totals=previous.totals if previous else TransferTotals(),
            recent_files=previous.recent_files if previous else [],
            checked_at=datetime.utcnow(),
            failure_streak=failure_streak,
        )
