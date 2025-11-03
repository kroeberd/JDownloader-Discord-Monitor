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
        print("⚠️ Kein Discord Webhook gesetzt.", flush=True)
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
        print(f"❌ Fehler beim Senden des Embeds: {e}", flush=True)

# --- Main Loop ---
def main():
    print("🚀 Starte JDownloader Discord Monitor (Unraid-ready, Multi-Device, Embeds, Footer, Logo, Avatar)...", flush=True)
    api = Myjdapi()
    try:
        api.connect(MYJD_EMAIL, MYJD_PASSWORD)
        print("✅ Verbunden mit MyJDownloader", flush=True)
    except Exception as e:
        print(f"❌ Login fehlgeschlagen: {e}", flush=True)
        return

    device_names = [d.strip() for d in MYJD_DEVICES.split(",")]
    print(f"⏱ Intervall: {INTERVAL} Sekunden", flush=True)

    # Speicher vorherige Bytes pro Gerät
    prev_bytes_dict = {}

    # Initialer Durchlauf zum Setzen von prev_bytes, ohne Embed zu senden
    for name in device_names:
        try:
            device = api.get_device(name)
            dl = device.downloads.query_links()
            prev_bytes_dict[name] = sum(f.get("bytesLoaded", 0) for f in dl)
        except Exception as e:
            print(f"⚠️ Fehler beim initialen Abruf von '{name}': {e}", flush=True)

    while True:
        start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{start_time}] 🚀 Starte neuen Durchlauf...", flush=True)

        for name in device_names:
            try:
                device = api.get_device(name)
                dl = device.downloads.query_links()
                done_bytes = sum(f.get("bytesLoaded", 0) for f in dl)

                total_speed = (done_bytes - prev_bytes_dict.get(name, 0)) / INTERVAL
                prev_bytes_dict[name] = done_bytes

                running = len(dl)
                total_size = sum(f.get("bytesTotal", 0) for f in dl)
                progress = (done_bytes / total_size * 100) if total_size > 0 else 0
                names = [f.get("name","?") for f in dl]
                downloaded_gb = done_bytes / 1e9
                total_gb = total_size / 1e9
                version = getattr(device,"version","-") or "-"
                platform = getattr(device,"platform","-") or "-"

                print(f"📡 {name}: {running} Downloads, {total_speed/1e6:.2f} MB/s, {progress:.1f}% Fortschritt", flush=True)
                send_discord_embed(name, running, total_speed, progress, names, downloaded_gb, total_gb, version, platform)

            except Exception as e:
                print(f"⚠️ Fehler bei Gerät '{name}': {e}", flush=True)

        print(f"⏳ Warten {INTERVAL} Sekunden bis zum nächsten Durchlauf...", flush=True)
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
