import os
import time
import datetime
import traceback
import requests
from myjdapi import Myjdapi


def format_bytes(size):
    """Konvertiert Bytes in lesbare Einheiten (GB, MB etc.)"""
    power = 2**10
    n = 0
    power_labels = {0: "", 1: "KB", 2: "MB", 3: "GB", 4: "TB"}
    while size > power and n < 4:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}"


def send_status_to_discord():
    webhook_url = os.getenv("WEBHOOK_URL")
    email = os.getenv("MYJD_EMAIL")
    password = os.getenv("MYJD_PASSWORD")
    devices = os.getenv("MYJD_DEVICES", "")
    device_list = [d.strip() for d in devices.split(",") if d.strip()]

    if not all([webhook_url, email, password, device_list]):
        raise ValueError("Fehlende Umgebungsvariablen: WEBHOOK_URL, MYJD_EMAIL, MYJD_PASSWORD oder MYJD_DEVICES")

    jd = Myjdapi()
    jd.connect(email, password)

    for device_name in device_list:
        try:
            device = jd.get_device(device_name)
            if not device:
                raise Exception(f"Kein Gerät gefunden mit Namen '{device_name}'")

            downloads = device.downloads.query_packages([])
            if not downloads:
                downloads = []

            total_speed = 0
            total_bytes = 0
            total_bytes_total = 0
            status_lines = []

            for pkg in downloads:
                name = pkg.get("name", "Unbekannt")
                bytes_loaded = pkg.get("bytesLoaded", 0)
                bytes_total = pkg.get("bytesTotal", 0)
                speed = pkg.get("speed", 0)

                total_bytes += bytes_loaded
                total_bytes_total += bytes_total
                total_speed += speed

                progress = 0
                if bytes_total > 0:
                    progress = bytes_loaded / bytes_total * 100

                status_lines.append(f"📦 **{name}** — {progress:.1f}% ({format_bytes(bytes_loaded)} / {format_bytes(bytes_total)})")

            version = device.device_info.get("version", "-")
            platform = device.device_info.get("os", "-")

            logo_url = "https://raw.githubusercontent.com/kroeberd/JDownloader-Discord-Monitor/refs/heads/main/logo.png"

            embed = {
                "username": "JDownloader Monitor",
                "avatar_url": logo_url,
                "embeds": [
                    {
                        "title": f"📡 JDownloader Status — {device_name}",
                        "color": 0x00BFFF,
                        "fields": [
                            {"name": "📊 Download-Geschwindigkeit", "value": f"{format_bytes(total_speed)}/s", "inline": True},
                            {"name": "💾 Heruntergeladen", "value": f"{format_bytes(total_bytes)} / {format_bytes(total_bytes_total)}", "inline": True},
                            {"name": "⚙️ Plattform", "value": platform, "inline": True},
                            {"name": "🔖 Version", "value": version, "inline": True},
                            {"name": "📂 Pakete", "value": "\n".join(status_lines) if status_lines else "Keine aktiven Downloads"},
                        ],
                        "footer": {
                            "text": "by kroeberd | Sarcasm",
                            "icon_url": logo_url
                        },
                        "timestamp": datetime.datetime.utcnow().isoformat()
                    }
                ]
            }

            requests.post(webhook_url, json=embed)

        except Exception as e:
            raise Exception(f"Fehler bei Gerät '{device_name}': {str(e)}")


def main():
    interval = int(os.getenv("INTERVAL", 600))  # Standard: 10 Minuten
    print(f"⏱️ Intervall eingestellt auf {interval} Sekunden")

    while True:
        start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{start_time}] 🚀 Sende Status an Discord...")

        try:
            send_status_to_discord()
            end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{end_time}] ✅ Status erfolgreich gesendet.")
        except Exception:
            error_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{error_time}] ⚠️ Fehler beim Statusabruf:\n{traceback.format_exc()}")

        print(f"⏳ Warte nun {interval} Sekunden bis zum nächsten Durchlauf...")
        time.sleep(interval)


if __name__ == "__main__":
    main()
