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

    # Gerätedatenfelder dynamisch erstellen
    device_fields = [
        {"name": "Status Gerät", "value": device_info['status'], "inline": True},
        {"name": "Plattform", "value": device_info['platform'], "inline": True},
        {"name": "Version", "value": device_info['version'], "inline": True},
    ]

    if device_info.get("uptime", 0) > 0:
        device_fields.append({"name": "Uptime", "value": str(datetime.timedelta(seconds=device_info['uptime'])), "inline": True})
    if device_info.get("diskSpace"):
        device_fields.append({"name": "Speicherplatz", "value": device_info['diskSpace'], "inline": True})
    if device_info.get("javaVersion"):
        device_fields.append({"name": "Java-Version", "value": device_info['javaVersion'], "inline": True})
    if device_info.get("lastActive"):
        device_fields.append({"name": "Letzte Aktivität", "value": str(device_info['lastActive']), "inline": True})

    # Download-Datenfelder dynamisch erstellen
    download_fields = []

    for key, label, value, inline in [
        ("active", "Downloads aktiv", download_info['active'], True),
        ("waiting", "Downloads wartend", download_info['waiting'], True),
        ("finished", "Downloads fertig", download_info['finished'], True),
        ("paused", "Pausierte Downloads", download_info['paused'], True),
        ("errors", "Fehlerhafte Downloads", download_info['errors'], True),
        ("speed", "Speed", download_info['speed'], True),
        ("progress", "Fortschritt", download_info['progress'], True),
        ("downloaded_gb", "Daten heruntergeladen", download_info['downloaded_gb'], True),
        ("total_gb", "Daten gesamt", download_info['total_gb'], True),
        ("links_total", "Links gesamt", download_info.get('links_total', 0), True)
    ]:
        if value and (not isinstance(value, (int, float)) or value != 0):
            if key == "speed":
                display_value = f"{value/1e6:.2f} MB/s"
            elif key == "progress":
                display_value = f"{value:.1f}%"
            elif key in ["downloaded_gb", "total_gb"]:
                display_value = f"{value:.2f} GB"
            else:
                display_value = str(value)
            download_fields.append({"name": label, "value": display_value, "inline": inline})

    # Dateinamen (max 5) immer anzeigen, oder – wenn keine
    download_fields.append({
        "name": "Dateien (max.5)",
        "value": "\n".join(f"• {n}" for n in download_info['names'][:5]) or "–",
        "inline": False
    })

    embed = {
        "username": "JDownloader Monitor",
        "avatar_url": LOGO_URL,
        "embeds": [
            {
                "title": f"📡 {device_info['name']}",
                "color": 0x00ff00,
                "fields": device_fields + download_fields,
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
                total_bytes = sum(f.get("bytesTotal", 0) for f in dl)
                speed = (done_bytes - prev_bytes_dict.get(name, 0)) / INTERVAL
                prev_bytes_dict[name] = done_bytes

                # Gerätedaten
                device_info = {
                    "name": getattr(device, "name", "?"),
                    "status": "ONLINE",
                    "version": getattr(device, "version", "-"),
                    "platform": getattr(device, "platform", "-"),
                    "uptime": getattr(device, "uptime", 0),
                    "diskSpace": getattr(device, "diskSpace", None),
                    "javaVersion": getattr(device, "javaVersion", None),
                    "lastActive": getattr(device, "lastActive", None)
                }

                # Downloads
                download_info = {
                    "active": sum(1 for f in dl if f.get("status") == "DOWNLOADING"),
                    "waiting": sum(1 for f in dl if f.get("status") == "WAITING"),
                    "finished": sum(1 for f in dl if f.get("status") == "FINISHED"),
                    "paused": sum(1 for f in dl if f.get("status") == "PAUSED"),
                    "errors": sum(1 for f in dl if f.get("status") == "ERROR"),
                    "speed": speed,
                    "progress": (done_bytes / total_bytes * 100) if total_bytes else 0,
                    "downloaded_gb": done_bytes / 1e9,
                    "total_gb": total_bytes / 1e9,
                    "names": [f.get("name", "?") for f in dl],
                    "links_total": len(dl)  # Gesamtzahl der Links
                }

                print(f"📡 {name}: {download_info['active']} active, {speed/1e6:.2f} MB/s, {download_info['progress']:.1f}% Fortschritt, {download_info['links_total']} Links gesamt", flush=True)
                send_discord_embed(device_info, download_info)

            except Exception as e:
                print(f"⚠️ Fehler bei Gerät '{name}': {e}", flush=True)

        print(f"⏳ Warten {INTERVAL} Sekunden bis zum nächsten Durchlauf...", flush=True)
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
