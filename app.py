import os
import time
import requests
from myjdapi import Myjdapi

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
MYJD_EMAIL = os.getenv("MYJD_EMAIL")
MYJD_PASSWORD = os.getenv("MYJD_PASSWORD")
MYJD_DEVICES = os.getenv("MYJD_DEVICES", "JDownloader")
INTERVAL = int(os.getenv("INTERVAL", "300"))
LOGO_URL = "https://raw.githubusercontent.com/kroeberd/JDownloader-Discord-Monitor/refs/heads/main/logo.png"

def send_discord_embed(name, running, total_speed, progress, names, downloaded_gb, total_gb, version, platform):
    if not WEBHOOK_URL:
        print("⚠️ Kein Discord Webhook gesetzt.")
        return
    embed = {
        "username": "JDownloader Monitor",
        "avatar_url": LOGO_URL,
        "embeds": [
            {
                "title": f"📡 {name}",
                "color": 0x00ff00,
                "fields": [
                    {"name": "Aktive Downloads", "value": str(running), "inline": True},
                    {"name": "Speed", "value": f"{total_speed/1e6:.2f} MB/s", "inline": True},
                    {"name": "Fortschritt", "value": f"{progress:.1f}%", "inline": True},
                    {"name": "Daten heruntergeladen", "value": f"{downloaded_gb:.2f} GB", "inline": True},
                    {"name": "Daten gesamt", "value": f"{total_gb:.2f} GB", "inline": True},
                    {"name": "Version", "value": version, "inline": True},
                    {"name": "Plattform", "value": platform, "inline": True},
                    {"name": "Dateien", "value": "\n".join(f"• {n}" for n in names[:5]) or "–", "inline": False}
                ],
                "footer": {
                    "text": "by kroeberd | Sarcasm",
                    "icon_url": LOGO_URL
                }
            }
        ]
    }
    try:
        requests.post(WEBHOOK_URL, json=embed)
    except Exception as e:
        print(f"❌ Fehler beim Senden des Embeds: {e}")

def get_status(device):
    dl = device.downloads.query_links()
    running = len(dl)
    total_speed = sum(f.get("bytesPerSecond", 0) for f in dl)
    total_size = sum(f.get("bytesTotal", 0) for f in dl)
    done = sum(f.get("bytesLoaded", 0) for f in dl)
    progress = (done / total_size * 100) if total_size > 0 else 0
    names = [f.get("name", "?") for f in dl]
    downloaded_gb = done / 1e9
    total_gb = total_size / 1e9
    version = getattr(device, "version", None) or "-"
    platform = getattr(device, "platform", None) or "-"
    return running, total_speed, progress, names, downloaded_gb, total_gb, version, platform

def main():
    print("🚀 Starte JDownloader Discord Monitor...")
    api = Myjdapi()
    try:
        api.connect(MYJD_EMAIL, MYJD_PASSWORD)
        print("✅ Verbunden mit MyJDownloader")
    except Exception as e:
        print(f"❌ Login fehlgeschlagen: {e}")
        return
    device_names = [d.strip() for d in MYJD_DEVICES.split(",")]
    while True:
        for name in device_names:
            try:
                device = api.get_device(name)
                status = get_status(device)
                running, total_speed, progress, names, downloaded_gb, total_gb, version, platform = status
                print(f"📡 {name}: {running} Downloads, {total_speed/1e6:.2f} MB/s, {progress:.1f}%")
                send_discord_embed(name, running, total_speed, progress, names, downloaded_gb, total_gb, version, platform)
            except Exception as e:
                print(f"⚠️ Fehler bei Gerät '{name}': {e}")
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
