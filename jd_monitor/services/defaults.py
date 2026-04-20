from __future__ import annotations

import os

from jd_monitor.schemas import AppConfig, CredentialsConfig, DeviceConfig, WebhookConfig


def slugify(value: str) -> str:
    cleaned = "".join(char.lower() if char.isalnum() else "-" for char in value.strip())
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-") or "item"


def default_config_from_env() -> AppConfig:
    language = os.getenv("LANG", "en").split(".")[0][:2].lower()
    locale = "de" if language == "de" else "en"
    interval = int(os.getenv("INTERVAL", "300"))
    raw_devices = [part.strip() for part in os.getenv("MYJD_DEVICES", "JDownloader").split(",") if part.strip()]
    device_models = [
        DeviceConfig(
            id=f"device-{slugify(name)}",
            name=name,
            display_name=name,
            poll_interval_seconds=interval,
        )
        for name in raw_devices
    ]

    webhooks: list[WebhookConfig] = []
    webhook_url = os.getenv("WEBHOOK_URL")
    if webhook_url:
        webhooks.append(
            WebhookConfig(
                id="webhook-default",
                name="Default Discord",
                url=webhook_url,
                device_ids=[device.id for device in device_models],
                notification_modes=["summary", "started", "completed", "offline"],
            )
        )
        for device in device_models:
            device.webhook_ids = ["webhook-default"]

    return AppConfig(
        locale=locale,  # type: ignore[arg-type]
        onboarding_completed=bool(webhook_url and os.getenv("MYJD_EMAIL") and os.getenv("MYJD_PASSWORD")),
        credentials=CredentialsConfig(
            email=os.getenv("MYJD_EMAIL", ""),
            password=os.getenv("MYJD_PASSWORD", ""),
        ),
        devices=device_models,
        webhooks=webhooks,
    )
