import asyncio

from jd_monitor.schemas import (
    AppConfig,
    ConnectivityConfig,
    CredentialsConfig,
    DeviceConfig,
    DeviceSnapshot,
    HealthStatus,
    TransferTotals,
    WebhookConfig,
)
from jd_monitor.services.connectivity import ConnectivityProbeResult
from jd_monitor.services.myjd import MyJdError
from jd_monitor.services.poller import PollerService


class FakeConfigRepo:
    def __init__(self, config: AppConfig) -> None:
        self._config = config

    def load(self) -> AppConfig:
        return self._config


class FakeDeviceRepo:
    def __init__(self, previous: DeviceSnapshot | None = None) -> None:
        self.previous = previous
        self.saved: DeviceSnapshot | None = None

    def list(self) -> list[DeviceSnapshot]:
        return [self.previous] if self.previous else []

    def get(self, device_id: str) -> DeviceSnapshot | None:
        return self.previous

    def save(self, snapshot: DeviceSnapshot) -> None:
        self.saved = snapshot


class FakeNotificationRepo:
    def list_recent(self, limit: int = 20) -> list:
        return []


class FailingMyJdService:
    async def fetch_snapshot(self, email: str, password: str, device: DeviceConfig) -> DeviceSnapshot:
        raise MyJdError("The JDownloader device is currently unavailable.", "simulated failure")


class ReachableConnectivityService:
    async def probe(self, device: DeviceConfig) -> ConnectivityProbeResult:
        return ConnectivityProbeResult(
            status="reachable",
            debug_message="simulated direct connectivity success",
        )


class FakeNotificationService:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []

    async def send(self, webhook: WebhookConfig, snapshot: DeviceSnapshot, event_type: str) -> None:
        self.sent.append((webhook.id, snapshot.device_id, event_type))


def test_poller_marks_device_degraded_when_local_probe_succeeds():
    device = DeviceConfig(
        id="device-1",
        name="JD2",
        display_name="JD2",
        poll_interval_seconds=300,
        webhook_ids=["wh-1"],
        connectivity=ConnectivityConfig(enabled=True, host="192.168.1.20", port=9666, timeout_seconds=2),
    )
    webhook = WebhookConfig(
        id="wh-1",
        name="Discord",
        url="https://discord.com/api/webhooks/test/test",
        device_ids=["device-1"],
        notification_modes=["error"],
    )
    previous = DeviceSnapshot(
        device_id="device-1",
        device_name="JD2",
        display_name="JD2",
        status="online",
        totals=TransferTotals(active=1, links_total=1),
    )
    config = AppConfig(
        credentials=CredentialsConfig(email="user@example.com", password="secret"),
        devices=[device],
        webhooks=[webhook],
    )
    device_repo = FakeDeviceRepo(previous)
    notifications = FakeNotificationService()
    poller = PollerService(
        FakeConfigRepo(config),
        device_repo,
        FakeNotificationRepo(),
        FailingMyJdService(),
        ReachableConnectivityService(),
        notifications,
    )

    asyncio.run(poller._poll_device(config, device))

    assert device_repo.saved is not None
    assert device_repo.saved.status == "degraded"
    assert device_repo.saved.connectivity_status == "reachable"
    assert device_repo.saved.connectivity_message == "Local endpoint reachable"
    assert poller.health == HealthStatus(status="degraded", message="MyJDownloader connectivity issues")
    assert notifications.sent == [("wh-1", "device-1", "error")]
