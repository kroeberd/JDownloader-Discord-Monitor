from __future__ import annotations

from jd_monitor.schemas import DeviceSnapshot, NotificationMode


def classify_event(previous: DeviceSnapshot | None, current: DeviceSnapshot) -> NotificationMode:
    if current.status in {"offline", "invalid_credentials"}:
        return "offline"
    if current.status == "degraded":
        return "error"
    if previous is None:
        return "summary"
    if previous.status != "online" and current.status == "online":
        return "summary"
    if previous.totals.active == 0 and current.totals.active > 0:
        return "started"
    if (
        previous.totals.active > 0
        and current.totals.active == 0
        and current.totals.finished >= previous.totals.finished
    ):
        return "completed"
    if current.totals.active == 0 and current.totals.waiting == 0 and current.totals.links_total == 0:
        return "idle"
    return "summary"
