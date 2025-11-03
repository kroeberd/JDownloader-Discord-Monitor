import os
import time
import datetime
import traceback
import requests
from myjdapi import Myjdapi

# === ENV Variablen ===
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
MYJD_EMAIL = os.getenv("MYJD_EMAIL")
MYJD_PASSWORD = os.getenv("MYJD_PASSWORD")
MYJD_DEVICES = os.getenv("MYJD_DEVICES", "JDownloader")  # Komma-separierte Liste
INTERVAL = int(os.getenv("INTERVAL", "300"))  # Sekunden

# Logo für Footer und Avatar (RAW-Link)
LOGO_URL = "https://raw.githubusercontent.com/kroeberd/JDownloader-Discord-Monitor/refs/heads/main/logo.png"

# --- Hilfsfunktionen ---
def format_bytes(size):
    power = 2**10
    n = 0
    units = {0:"B",1:"KB",2:"MB",3:"GB",4:"TB"}
    while size > power and n < 4:
        size /= power
        n += 1
    return f"{size:.2f} {units[n]}"

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
                },
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        ]
    }

    try:
        requests.post(WEBHOOK_URL, json=embed)
    except Exception as e:
        print(f"❌ Fehler beim Senden des Embeds: {e}")

def get_status(device, prev_bytes):
    """Liest Status von JDownloader und berechnet Geschwindigkeit über INTERVAL"""
    dl = device.downloads.query_links()
    running = len(dl)
    total_size = sum(f.get("bytesTotal", 0) for f in dl)
    done = sum(f.get("bytesLoaded", 0) for f in dl)
    progress = (done / total_size * 100) if total_size > 0 else 0
    names = [f.get("name", "?") for f in dl]

    downloaded_gb = done / 1e9
    total_gb = total_size / 1e9

    version = getattr(device, "version", None) or "-"
    platform = getattr(device, "platform", None) or "-"

    # Berechne Geschwindigkeit über INTERVAL
    total_speed = (done - prev_bytes) / INTERVAL if prev_bytes is not None else 0

    return running, total_speed, progress, names, downloaded_gb, total_gb, version, platform, done

# --- Main Loop ---
def main():
    print("🚀 Starte JDownloader Discord Monitor (Multi-Device + Embeds + Footer + Logo + Avatar)...")
    api = Myjdapi()
    try:
        api.connect(MYJD_EMAIL, MYJD_PASSWORD)
        print("✅ Verbunden mit MyJDownloader")
    except Exception as e:
        print(f"❌ Login fehlgeschlagen: {e}")
        return

    device_names = [d.strip() for d in MYJD_DEVICES.split(",")]
    print(f"⏱ Intervall: {INTERVAL} Sekunden")

    # Speicher vorherige bytesLoaded pro Gerät
    prev_bytes_dict = {name: None for name in device_names}

    while True:
        start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{start_time}] 🚀 Starte neuen Durchlauf...")

        for name in device_names:
            try:
                device = api.get_device(name)
                status = get_status(device, prev_bytes_dict[name])
                running, total_speed, progress, names, downloaded_gb, total_gb, version, platform, done_bytes = status

                prev_bytes_dict[name] = done_bytes  # Speichere für nächste Runde

                print(f"📡 {name}: {running} Downloads, {total_speed/1e6:.2f} MB/s, {progress:.1f}% Fortschritt")
                send_discord_embed(name, running, total_speed, progress, names, downloaded_gb, total_gb, version, platform)

            except Exception as e:
                print(f"⚠️ Fehler bei Gerät '{name}': {e}")

        print(f"⏳ Warten {INTERVAL} Sekunden bis zum nächsten Durchlauf...")
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
