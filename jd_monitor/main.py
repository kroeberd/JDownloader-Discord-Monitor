from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from jd_monitor.api import router
from jd_monitor.db import init_db
from jd_monitor.log_setup import configure_logging, memory_logs
from jd_monitor.repo_utils import ConfigRepository, DeviceStateRepository, NotificationRepository
from jd_monitor.schemas import DeviceSnapshot, TransferTotals
from jd_monitor.services.defaults import default_config_from_env
from jd_monitor.services.myjd import MyJDownloaderService
from jd_monitor.services.notifications import NotificationService
from jd_monitor.services.poller import PollerService
from jd_monitor.settings import settings


@dataclass
class AppServices:
    config_repo: ConfigRepository
    device_repo: DeviceStateRepository
    notification_repo: NotificationRepository
    myjd: MyJDownloaderService
    notifications: NotificationService
    poller: PollerService
    logs = memory_logs

    @staticmethod
    def sample_snapshot() -> DeviceSnapshot:
        return DeviceSnapshot(
            device_id="sample-device",
            device_name="Sample JD",
            display_name="Sample JD",
            status="online",
            message="Preview generated from sample data.",
            platform="linux",
            version="2.0",
            uptime_seconds=86400,
            totals=TransferTotals(
                active=2,
                waiting=3,
                finished=12,
                paused=1,
                errors=0,
                speed_bytes_per_second=18_400_000,
                progress_percent=67.4,
                downloaded_bytes=54_000_000_000,
                total_bytes=80_000_000_000,
                links_total=18,
            ),
            recent_files=[],
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_dirs()
    configure_logging(settings.log_path, "INFO")
    init_db()

    config_repo = ConfigRepository()
    if config_repo.load() is None:
        config_repo.save(default_config_from_env())

    device_repo = DeviceStateRepository()
    notification_repo = NotificationRepository()
    myjd = MyJDownloaderService()
    notifications = NotificationService(notification_repo)
    poller = PollerService(config_repo, device_repo, notification_repo, myjd, notifications)

    app.state.services = AppServices(
        config_repo=config_repo,
        device_repo=device_repo,
        notification_repo=notification_repo,
        myjd=myjd,
        notifications=notifications,
        poller=poller,
    )
    await poller.start()
    yield
    await poller.stop()
    await notifications.close()


app = FastAPI(title="JDownloader Monitor", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="jd_monitor/static"), name="static")
app.include_router(router)
