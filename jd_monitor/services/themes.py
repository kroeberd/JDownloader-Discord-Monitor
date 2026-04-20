from __future__ import annotations

import hashlib
from datetime import datetime

from jd_monitor import __version__
from jd_monitor.schemas import DeviceSnapshot, LocaleName, NotificationMode, PreviewResponse, WebhookConfig
from jd_monitor.services.formatting import format_bytes, format_speed, format_uptime
from jd_monitor.services.localization import EVENT_TITLES, tr

THEMES: dict[str, dict[str, str]] = {
    "minimal": {"label": "Minimal", "description": "Lean summary with only the key transfer numbers."},
    "modern": {"label": "Modern", "description": "Balanced default for daily monitoring."},
    "compact": {"label": "Compact", "description": "Tighter layout for busy Discord channels."},
    "detailed": {"label": "Detailed", "description": "Expanded operational view with richer status data."},
    "status-card": {"label": "Status Card", "description": "Card-like presentation focused on health."},
    "high-contrast": {"label": "High Contrast", "description": "Bold accessibility-first colors."},
    "homelab": {"label": "Homelab", "description": "Utility dashboard styling for self-hosters."},
}

THEME_COLORS = {
    "minimal": 0x7E8AA0,
    "modern": 0x58A6FF,
    "compact": 0x2EA043,
    "detailed": 0xD29922,
    "status-card": 0x1F6FEB,
    "high-contrast": 0xFF7B72,
    "homelab": 0x3FB950,
}


def available_themes() -> list[dict[str, str]]:
    return [{"id": key, **value} for key, value in THEMES.items()]


def _fields(locale: LocaleName, snapshot: DeviceSnapshot, webhook: WebhookConfig) -> list[dict]:
    customization = webhook.customization
    totals = snapshot.totals
    fields: list[dict] = []
    if customization.show_connection_badge:
        fields.append({"name": tr(locale, "status"), "value": snapshot.status.title(), "inline": True})
    if customization.show_device_details:
        for name, value in [
            (tr(locale, "platform"), snapshot.platform),
            (tr(locale, "version"), snapshot.version),
            (tr(locale, "uptime"), format_uptime(snapshot.uptime_seconds)),
            (tr(locale, "disk"), format_bytes(snapshot.disk_free_bytes)),
        ]:
            if value and value != "-":
                fields.append({"name": name, "value": str(value), "inline": True})
    if customization.show_transfer_stats:
        fields.extend(
            [
                {"name": tr(locale, "active"), "value": str(totals.active), "inline": True},
                {"name": tr(locale, "waiting"), "value": str(totals.waiting), "inline": True},
                {"name": tr(locale, "finished"), "value": str(totals.finished), "inline": True},
                {"name": tr(locale, "paused"), "value": str(totals.paused), "inline": True},
                {"name": tr(locale, "errors"), "value": str(totals.errors), "inline": True},
                {"name": tr(locale, "speed"), "value": format_speed(totals.speed_bytes_per_second), "inline": True},
                {"name": tr(locale, "progress"), "value": f"{totals.progress_percent:.1f}%", "inline": True},
                {"name": tr(locale, "downloaded"), "value": format_bytes(totals.downloaded_bytes), "inline": True},
                {"name": tr(locale, "total"), "value": format_bytes(totals.total_bytes), "inline": True},
            ]
        )
    if customization.show_recent_files and snapshot.recent_files:
        file_lines = [f"- {entry.name}" for entry in snapshot.recent_files]
        fields.append({"name": tr(locale, "recent_files"), "value": "\n".join(file_lines), "inline": False})
    return [field for field in fields if field["value"] not in {"", "0.0 B"}]


def render_payload(webhook: WebhookConfig, snapshot: DeviceSnapshot, event_type: NotificationMode) -> dict:
    locale = webhook.locale
    title = tr(locale, EVENT_TITLES[event_type])
    footer_text = f"JD - Monitor • {snapshot.display_name} • {__version__}"
    payload = {
        "username": webhook.branding.username,
        "avatar_url": webhook.branding.avatar_url,
        "embeds": [
            {
                "title": f"{title} • {snapshot.display_name}",
                "description": snapshot.message or f"{snapshot.display_name} is {snapshot.status}.",
                "color": THEME_COLORS[webhook.theme],
                "fields": _fields(locale, snapshot, webhook),
                "footer": {"text": footer_text},
                "timestamp": snapshot.checked_at.isoformat(),
            }
        ],
    }
    return payload


def fingerprint_payload(payload: dict) -> str:
    return hashlib.sha256(repr(payload).encode("utf-8")).hexdigest()


def render_preview(webhook: WebhookConfig, snapshot: DeviceSnapshot, event_type: NotificationMode) -> PreviewResponse:
    payload = render_payload(webhook, snapshot, event_type)
    embed = payload["embeds"][0]
    fields_html = "".join(
        (
            f"<div class='preview-field{' wide' if not field['inline'] else ''}'>"
            f"<span>{field['name']}</span><strong>{field['value']}</strong></div>"
        )
        for field in embed["fields"]
    )
    footer_html = (
        f"<div class='discord-preview-footer'>{embed['footer']['text']} • "
        f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</div>"
    )
    html = (
        "<div class='discord-preview-card'>"
        f"<div class='discord-preview-accent theme-{webhook.theme}'></div>"
        f"<div class='discord-preview-header'><h4>{embed['title']}</h4><p>{embed['description']}</p></div>"
        f"<div class='discord-preview-fields'>{fields_html}</div>"
        f"{footer_html}"
        "</div>"
    )
    return PreviewResponse(payload=payload, html=html)
