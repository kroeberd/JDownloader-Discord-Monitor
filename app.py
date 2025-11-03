import os
import time
import datetime
import requests
from myjdapi import Myjdapi

# === ENV Variablen ===
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
MYJD_EMAIL = os.getenv("MYJD_EMAIL")
MYJD_PASSWORD = os.getenv("MYJD_PASSWORD")
MYJD_DEVICES = os.getenv("MYJD_DEVICES", "JDownloader")  # Komma-separierte Liste
INTERVAL = int(os.getenv("INTERVAL", "300"))  # Sekunden

LOGO_URL = "https://raw.githubusercontent.com/kroeberd/JDownloader-Discord-Monitor/refs/heads/main/logo.png"

# --- Discord Embed ---
def send_discord_embed(device_info, download_info):
    if not WEBHOOK_URL:
        print("⚠️ Kein Discord Webhook gesetzt.", flush=True)
        return

    embed = {
        "username": "JDownloader Monitor",
        "avatar_url": LOGO_URL,
        "embeds": [
            {
                "title": f"📡 {device_info['name']}",
                "color": 0x00ff00,
                "fields": [
                    {"name": "Status Gerät", "value": device_info['status'], "inline": True},
                    {"name": "Plattform", "value": device_info['platform'], "inline": True},
                    {"name": "Version", "value": device_info['version'], "inline": True},
                    {"name": "Uptime", "value": str(datetime.timedelta(seconds=device_info['uptime'])), "inline": True},
                    {"name": "Speicherplatz", "value": device_info.get('diskSpace','-'), "inline": True},
                    {"name": "Java-Version", "value": device_info.get('javaVersion','-'), "inline": True},
                    {"name": "Letzte Aktivität", "value": str(device_info.get('lastActive','-')), "inline": True},

                    {"name": "Downloads aktiv", "value": str(download_info['active']), "inline": True},
                    {"name": "Downloads wartend", "value": str(download_info['waiting']), "inline": True},
                    {"name": "Downloads fertig", "value": str(download_info['finished']), "inline": True},
                    {"name": "Pausierte Downloads", "value": str(download_info['paused']), "inline": True},
                    {"name": "Fehlerhafte Downloads", "value": str(download_info['errors']), "inline": True},
                    {"name": "Speed", "value": f"{download_info['speed']/1e6:.2f} MB/s", "inline": True},
                    {"name": "Fortschritt", "value": f"{download_info['progress']:.1f}%", "inline": True},
                    {"name": "Daten heruntergeladen", "value": f"{download_info['downloaded_gb']:.2f} GB", "inline": True},
                    {"name": "Daten gesamt", "value": f"{download_info['total_gb']:.2f} GB", "inline": True},
                    {"name": "Dateien (max.5)", "value": "\n".join(f"• {n}" for n in download_info['names'][:5]) or "–", "inline": False}
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

# --- Main ---
def main():
    print("🚀 Starte JDownloader Discord Monitor...", flush=True)
    api = Myjdapi()
    try:
        api.connect(MYJD_EMAIL, MYJD_PASSWORD)
        print("✅ Verbunden mit MyJDownloader", flush=True)
    except Exception as e:
        print(f"❌ Login fehlgeschlagen: {e}", flush=True)
        return

    device_names = [d.strip() for d in MYJD_DEVICES.split(",")]
    print(f"⏱ Intervall: {INTERVAL} Sekunden", flush=True)

    prev_bytes_dict = {}

    # Initialer Durchlauf zum Setzen der Bytes
    for name in device_names:
        try:
            device = api.get_device(name)
            dl = device.downloads.query_links()
            prev_bytes_dict[name] = sum(f.get("bytesLoaded",0) for f in dl)
        except Exception as e:
            print(f"⚠️ Fehler beim initialen Abruf von '{name}': {e}", flush=True)

    while True:
        start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{start_time}] 🚀 Starte neuen Durchlauf...", flush=True)

        for name in device_names:
            try:
                device = api.get_device(name)

                dl = device.downloads.query_links()
                done_bytes = sum(f.get("bytesLoaded",0) for f in dl)
                speed = (done_bytes - prev_bytes_dict.get(name,0))/INTERVAL
                prev_bytes_dict[name] = done_bytes

                # Gerätedaten (abwärtskompatibel)
                device_info = {
                    "name": getattr(device, "name", "?"),
                    "status": "ONLINE",  # Standard, da alte myjdapi Versionen kein Status liefern
                    "version": getattr(device, "version", "-"),
                    "platform": getattr(device, "platform", "-"),
                    "uptime": getattr(device, "uptime", 0),
                    "diskSpace": getattr(device, "diskSpace", "-"),
                    "javaVersion": getattr(device, "javaVersion", "-"),
                    "lastActive": getattr(device, "lastActive", "-")
                }

                # Downloads
                download_info = {
                    "active": sum(1 for f in dl if f.get("status")=="DOWNLOADING"),
                    "waiting": sum(1 for f in dl if f.get("status")=="WAITING"),
                    "finished": sum(1 for f in dl if f.get("status")=="FINISHED"),
                    "paused": sum(1 for f in dl if f.get("status")=="PAUSED"),
                    "errors": sum(1 for f in dl if f.get("status")=="ERROR"),
                    "speed": speed,
                    "progress": (done_bytes/sum(f.get("bytesTotal",0) for f in dl)*100) if dl else 0,
                    "downloaded_gb": done_bytes/1e9,
                    "total_gb": sum(f.get("bytesTotal",0) for f in dl)/1e9,
                    "names": [f.get("name","?") for f in dl]
                }

                print(f"📡 {name}: {download_info['active']} active, {speed/1e6:.2f} MB/s, {download_info['progress']:.1f}% Fortschritt", flush=True)
                send_discord_embed(device_info, download_info)

            except Exception as e:
                print(f"⚠️ Fehler bei Gerät '{name}': {e}", flush=True)

        print(f"⏳ Warten {INTERVAL} Sekunden bis zum nächsten Durchlauf...", flush=True)
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
