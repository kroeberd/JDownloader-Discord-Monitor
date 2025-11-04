import os
import time
import datetime
import requests
from myjdapi import Myjdapi

# === ENV Variablen ===
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
MYJD_EMAIL = os.getenv("MYJD_EMAIL")
MYJD_PASSWORD = os.getenv("MYJD_PASSWORD")
MYJD_DEVICES = os.getenv("MYJD_DEVICES", "JDownloader")
INTERVAL = int(os.getenv("INTERVAL", "300"))
LANG = os.getenv("LANG", "de").lower()  # "de" oder "en"

LOGO_URL = "https://raw.githubusercontent.com/kroeberd/JDownloader-Discord-Monitor/refs/heads/main/logos/logo_jm_128px.png"

# --- Mehrsprachige Texte ---
TEXTS = {
    "de": {
        "starting": "🚀 Starte JDownloader Discord Monitor...",
        "connected": "✅ Verbunden mit MyJDownloader",
        "login_failed": "❌ Login fehlgeschlagen",
        "interval": "⏱ Intervall",
        "start_run": "🚀 Starte neuen Durchlauf...",
        "waiting": "⏳ Warten {interval} Sekunden bis zum nächsten Durchlauf...",
        "reconnect": "🔐 Token ungültig, erneuter Login...",
        "reconnect_ok": "✅ Reconnect erfolgreich!",
        "reconnect_fail": "❌ Reconnect fehlgeschlagen",
        "error_device": "⚠️ Fehler bei Gerät",
        "device_status": "📡 Status Gerät",
        "platform": "💻 Plattform",
        "version": "🏷️ Version",
        "uptime": "⏱️ Uptime",
        "disk": "💾 Speicherplatz",
        "java": "☕ Java-Version",
        "last_active": "🕒 Letzte Aktivität",
        "downloads_active": "⬇️ Downloads aktiv",
        "downloads_wait": "⏳ Downloads wartend",
        "downloads_done": "✅ Downloads fertig",
        "downloads_paused": "⏸️ Pausierte Downloads",
        "downloads_error": "❌ Fehlerhafte Downloads",
        "speed": "⚡ Geschwindigkeit",
        "progress": "📊 Fortschritt",
        "downloaded": "📥 Daten heruntergeladen",
        "total": "📦 Daten gesamt",
        "links": "🔗 Links gesamt",
        "files": "📄 Zuletzt aktive Dateien (max. 5)",
    },
    "en": {
        "starting": "🚀 Starting JDownloader Discord Monitor...",
        "connected": "✅ Connected to MyJDownloader",
        "login_failed": "❌ Login failed",
        "interval": "⏱ Interval",
        "start_run": "🚀 Starting new cycle...",
        "waiting": "⏳ Waiting {interval} seconds until next check...",
        "reconnect": "🔐 Token invalid, re-login...",
        "reconnect_ok": "✅ Reconnect successful!",
        "reconnect_fail": "❌ Reconnect failed",
        "error_device": "⚠️ Error on device",
        "device_status": "📡 Device Status",
        "platform": "💻 Platform",
        "version": "🏷️ Version",
        "uptime": "⏱️ Uptime",
        "disk": "💾 Disk Space",
        "java": "☕ Java Version",
        "last_active": "🕒 Last Active",
        "downloads_active": "⬇️ Active Downloads",
        "downloads_wait": "⏳ Waiting Downloads",
        "downloads_done": "✅ Finished Downloads",
        "downloads_paused": "⏸️ Paused Downloads",
        "downloads_error": "❌ Failed Downloads",
        "speed": "⚡ Speed",
        "progress": "📊 Progress",
        "downloaded": "📥 Data Downloaded",
        "total": "📦 Total Data",
        "links": "🔗 Total Links",
        "files": "📄 Recently Active Files (max. 5)",
    }
}

T = TEXTS[LANG]


# --- Discord Embed ---
def send_discord_embed(device_info, download_info):
    if not WEBHOOK_URL:
        print("⚠️ Kein Discord Webhook gesetzt." if LANG == "de" else "⚠️ No Discord webhook set.", flush=True)
        return

    device_fields = [
        {"name": T["device_status"], "value": device_info["status"], "inline": True},
        {"name": T["platform"], "value": device_info["platform"], "inline": True},
        {"name": T["version"], "value": device_info["version"], "inline": True},
    ]

    if device_info.get("uptime", 0) > 0:
        device_fields.append({
            "name": T["uptime"],
            "value": str(datetime.timedelta(seconds=device_info["uptime"])),
            "inline": True
        })
    if device_info.get("diskSpace"):
        device_fields.append({"name": T["disk"], "value": device_info["diskSpace"], "inline": True})
    if device_info.get("javaVersion"):
        device_fields.append({"name": T["java"], "value": device_info["javaVersion"], "inline": True})
    if device_info.get("lastActive"):
        device_fields.append({"name": T["last_active"], "value": str(device_info["lastActive"]), "inline": True})

    download_fields = []
    for key, label, value, inline in [
        ("active", T["downloads_active"], download_info["active"], True),
        ("waiting", T["downloads_wait"], download_info["waiting"], True),
        ("finished", T["downloads_done"], download_info["finished"], True),
        ("paused", T["downloads_paused"], download_info["paused"], True),
        ("errors", T["downloads_error"], download_info["errors"], True),
        ("speed", T["speed"], download_info["speed"], True),
        ("progress", T["progress"], download_info["progress"], True),
        ("downloaded_gb", T["downloaded"], download_info["downloaded_gb"], True),
        ("total_gb", T["total"], download_info["total_gb"], True),
        ("links_total", T["links"], download_info.get("links_total", 0), True),
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

    download_fields.append({
        "name": T["files"],
        "value": "\n".join(f"• {n}" for n in download_info["names"][-5:]) or "–",
        "inline": False,
    })

    embed = {
        "username": "JDownloader Monitor",
        "avatar_url": LOGO_URL,
        "embeds": [
            {
                "title": f"📡 {device_info['name']}",
                "color": 0x00ff00,
                "fields": device_fields + download_fields,
                "footer": {"text": "by kroeberd | Sarcasm", "icon_url": LOGO_URL},
                "timestamp": datetime.datetime.utcnow().isoformat(),
            }
        ],
    }

    try:
        requests.post(WEBHOOK_URL, json=embed)
    except Exception as e:
        print(f"❌ Fehler beim Senden des Embeds: {e}", flush=True)


# --- Main ---
def main():
    print(T["starting"], flush=True)
    api = Myjdapi()
    try:
        api.connect(MYJD_EMAIL, MYJD_PASSWORD)
        print(T["connected"], flush=True)
    except Exception as e:
        print(f"{T['login_failed']}: {e}", flush=True)
        return

    device_names = [d.strip() for d in MYJD_DEVICES.split(",")]
    print(f"{T['interval']}: {INTERVAL} s", flush=True)

    prev_bytes_dict = {}

    for name in device_names:
        try:
            device = api.get_device(name)
            dl = device.downloads.query_links()
            prev_bytes_dict[name] = sum(f.get("bytesLoaded", 0) for f in dl)
        except Exception as e:
            print(f"⚠️ Fehler beim initialen Abruf von '{name}': {e}", flush=True)

    while True:
        start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{start_time}] {T['start_run']}", flush=True)

        for name in device_names:
            try:
                try:
                    device = api.get_device(name)
                    dl = device.downloads.query_links()
                except Exception as e:
                    if "TOKEN_INVALID" in str(e):
                        print(T["reconnect"], flush=True)
                        try:
                            api.connect(MYJD_EMAIL, MYJD_PASSWORD)
                            device = api.get_device(name)
                            dl = device.downloads.query_links()
                            print(T["reconnect_ok"], flush=True)
                        except Exception as e2:
                            print(f"{T['reconnect_fail']}: {e2}", flush=True)
                            continue
                    else:
                        raise

                done_bytes = sum(f.get("bytesLoaded", 0) for f in dl)
                total_bytes = sum(f.get("bytesTotal", 0) for f in dl)
                speed = (done_bytes - prev_bytes_dict.get(name, 0)) / INTERVAL
                prev_bytes_dict[name] = done_bytes

                device_info = {
                    "name": getattr(device, "name", "?"),
                    "status": "ONLINE",
                    "version": getattr(device, "version", "-"),
                    "platform": getattr(device, "platform", "-"),
                    "uptime": getattr(device, "uptime", 0),
                    "diskSpace": getattr(device, "diskSpace", None),
                    "javaVersion": getattr(device, "javaVersion", None),
                    "lastActive": getattr(device, "lastActive", None),
                }

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
                    "links_total": len(dl),
                }

                print(
                    f"📡 {name}: {download_info['active']} active, "
                    f"{speed/1e6:.2f} MB/s, {download_info['progress']:.1f}%, "
                    f"{download_info['links_total']} links",
                    flush=True,
                )

                send_discord_embed(device_info, download_info)

            except Exception as e:
                print(f"{T['error_device']} '{name}': {e}", flush=True)

        print(T["waiting"].format(interval=INTERVAL), flush=True)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
