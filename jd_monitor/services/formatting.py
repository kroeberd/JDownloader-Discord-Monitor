from __future__ import annotations

from datetime import timedelta


def format_bytes(value: int | None) -> str:
    if value is None:
        return "-"
    units = ["B", "KB", "MB", "GB", "TB"]
    result = float(value)
    for unit in units:
        if result < 1024 or unit == units[-1]:
            return f"{result:.1f} {unit}"
        result /= 1024
    return f"{value} B"


def format_speed(value: float) -> str:
    return f"{value / 1024 / 1024:.2f} MB/s"


def format_uptime(seconds: int | None) -> str:
    if seconds is None:
        return "-"
    return str(timedelta(seconds=seconds))
