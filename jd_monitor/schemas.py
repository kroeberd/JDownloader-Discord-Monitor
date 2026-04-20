from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

ThemeName = Literal[
    "minimal",
    "modern",
    "compact",
    "detailed",
    "status-card",
    "high-contrast",
    "homelab",
]
LocaleName = Literal["en", "de"]
NotificationMode = Literal["summary", "started", "completed", "idle", "offline", "error"]


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _validate_timezone(value: str) -> str:
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Unknown timezone: {value}") from exc
    return value


class QuietHoursConfig(BaseModel):
    enabled: bool = False
    start: str = "23:00"
    end: str = "07:00"
    timezone: str = "Europe/Berlin"

    _timezone = field_validator("timezone")(_validate_timezone)


class CredentialsConfig(BaseModel):
    email: str = ""
    password: str = ""


class ConnectivityConfig(BaseModel):
    enabled: bool = False
    host: str | None = None
    port: int = Field(default=9666, ge=1, le=65535)
    timeout_seconds: int = Field(default=3, ge=1, le=15)

    @field_validator("host", mode="before")
    @classmethod
    def normalize_host(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class BrandingConfig(BaseModel):
    username: str = "JDownloader Monitor"
    avatar_url: str | None = None


class ThemeCustomization(BaseModel):
    accent_color: str | None = "#58a6ff"
    accent_icon: str | None = "satellite"
    compact: bool = False
    verbose: bool = True
    show_device_details: bool = True
    show_transfer_stats: bool = True
    show_recent_files: bool = True
    show_connection_badge: bool = True


class DeviceConfig(BaseModel):
    id: str
    name: str
    display_name: str | None = None
    enabled: bool = True
    poll_interval_seconds: int = Field(default=300, ge=30, le=3600)
    webhook_ids: list[str] = Field(default_factory=list)
    summary_interval_minutes: int = Field(default=30, ge=5, le=1440)
    quiet_hours: QuietHoursConfig = Field(default_factory=QuietHoursConfig)
    connectivity: ConnectivityConfig = Field(default_factory=ConnectivityConfig)


class WebhookConfig(BaseModel):
    id: str
    name: str
    url: HttpUrl
    enabled: bool = True
    device_ids: list[str] = Field(default_factory=list)
    theme: ThemeName = "modern"
    locale: LocaleName = "en"
    branding: BrandingConfig = Field(default_factory=BrandingConfig)
    customization: ThemeCustomization = Field(default_factory=ThemeCustomization)
    notification_modes: list[NotificationMode] = Field(default_factory=lambda: ["summary"])
    throttle_seconds: int = Field(default=180, ge=30, le=86400)


class AppConfig(BaseModel):
    locale: LocaleName = "en"
    timezone: str = "Europe/Berlin"
    onboarding_completed: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    credentials: CredentialsConfig = Field(default_factory=CredentialsConfig)
    devices: list[DeviceConfig] = Field(default_factory=list)
    webhooks: list[WebhookConfig] = Field(default_factory=list)

    _timezone = field_validator("timezone")(_validate_timezone)

    @model_validator(mode="after")
    def validate_links(self) -> AppConfig:
        device_ids = {device.id for device in self.devices}
        webhook_ids = {webhook.id for webhook in self.webhooks}
        for device in self.devices:
            unknown = set(device.webhook_ids) - webhook_ids
            if unknown:
                raise ValueError(f"Device {device.id} references unknown webhooks: {sorted(unknown)}")
        for webhook in self.webhooks:
            unknown = set(webhook.device_ids) - device_ids
            if unknown:
                raise ValueError(f"Webhook {webhook.id} references unknown devices: {sorted(unknown)}")
        return self


class TransferTotals(BaseModel):
    active: int = 0
    waiting: int = 0
    finished: int = 0
    paused: int = 0
    errors: int = 0
    speed_bytes_per_second: float = 0.0
    progress_percent: float = 0.0
    downloaded_bytes: int = 0
    total_bytes: int = 0
    links_total: int = 0


class DownloadEntry(BaseModel):
    name: str
    status: str = "UNKNOWN"
    bytes_loaded: int = 0
    bytes_total: int = 0
    eta_seconds: int | None = None


class DeviceSnapshot(BaseModel):
    device_id: str
    device_name: str
    display_name: str
    status: Literal["online", "offline", "degraded", "invalid_credentials", "unknown"] = "unknown"
    message: str = ""
    platform: str | None = None
    version: str | None = None
    uptime_seconds: int | None = None
    disk_free_bytes: int | None = None
    java_version: str | None = None
    last_active_at: datetime | None = None
    connectivity_status: Literal["unknown", "unconfigured", "reachable", "unreachable"] = "unknown"
    connectivity_message: str | None = None
    totals: TransferTotals = Field(default_factory=TransferTotals)
    recent_files: list[DownloadEntry] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=utc_now)
    failure_streak: int = 0


class NotificationAttempt(BaseModel):
    webhook_id: str
    device_id: str
    event_type: NotificationMode
    fingerprint: str
    delivered: bool
    delivered_at: datetime = Field(default_factory=utc_now)
    status_code: int | None = None
    error_class: str | None = None
    error_message: str | None = None


class HealthStatus(BaseModel):
    status: Literal["ok", "degraded", "error"]
    message: str
    checked_at: datetime = Field(default_factory=utc_now)
    details: dict[str, str] = Field(default_factory=dict)


class DashboardSummary(BaseModel):
    health: HealthStatus
    config: AppConfig
    devices: list[DeviceSnapshot]
    last_audit_events: list[NotificationAttempt]
    themes: list[dict[str, str]]


class PreviewRequest(BaseModel):
    webhook: WebhookConfig
    snapshot: DeviceSnapshot | None = None
    event_type: NotificationMode = "summary"


class PreviewResponse(BaseModel):
    payload: dict
    html: str


class TestWebhookRequest(BaseModel):
    webhook: WebhookConfig
    snapshot: DeviceSnapshot | None = None


class LogLine(BaseModel):
    ts: datetime
    level: str
    logger: str
    message: str
    extra: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
