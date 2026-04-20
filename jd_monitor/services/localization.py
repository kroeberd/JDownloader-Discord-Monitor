from __future__ import annotations

from jd_monitor.schemas import LocaleName, NotificationMode

STRINGS: dict[LocaleName, dict[str, str]] = {
    "en": {
        "summary_title": "JDownloader status",
        "started_title": "Download activity started",
        "completed_title": "Downloads completed",
        "idle_title": "Device is idle",
        "offline_title": "Device is offline",
        "error_title": "Device error",
        "status": "Status",
        "platform": "Platform",
        "version": "Version",
        "uptime": "Uptime",
        "disk": "Disk",
        "connectivity": "Connectivity",
        "speed": "Speed",
        "progress": "Progress",
        "active": "Active",
        "waiting": "Waiting",
        "finished": "Finished",
        "paused": "Paused",
        "errors": "Errors",
        "downloaded": "Downloaded",
        "total": "Total",
        "recent_files": "Recent files",
    },
    "de": {
        "summary_title": "JDownloader Status",
        "started_title": "Download-Aktivitaet gestartet",
        "completed_title": "Downloads abgeschlossen",
        "idle_title": "Geraet ist inaktiv",
        "offline_title": "Geraet ist offline",
        "error_title": "Geraetefehler",
        "status": "Status",
        "platform": "Plattform",
        "version": "Version",
        "uptime": "Laufzeit",
        "disk": "Speicher",
        "connectivity": "Konnektivitaet",
        "speed": "Geschwindigkeit",
        "progress": "Fortschritt",
        "active": "Aktiv",
        "waiting": "Wartend",
        "finished": "Fertig",
        "paused": "Pausiert",
        "errors": "Fehler",
        "downloaded": "Heruntergeladen",
        "total": "Gesamt",
        "recent_files": "Letzte Dateien",
    },
}


EVENT_TITLES: dict[NotificationMode, str] = {
    "summary": "summary_title",
    "started": "started_title",
    "completed": "completed_title",
    "idle": "idle_title",
    "offline": "offline_title",
    "error": "error_title",
}


def tr(locale: LocaleName, key: str) -> str:
    return STRINGS[locale][key]
