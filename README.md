# JDownloader Discord Monitor

Dieses Projekt überwacht **eine oder mehrere JDownloader-Instanzen** über MyJDownloader und sendet regelmäßig **Statusmeldungen an Discord**.

Projekt hat noch **Beta**-Status.

Die Meldungen erscheinen als **schöne Discord-Embeds** mit:

- Aktiven Downloads
- Download-Geschwindigkeit
- Fortschritt (%)
- Daten heruntergeladen (GB)
- Gesamtdaten (GB)
- Version von JDownloader
- Plattform
- Bis zu 5 Dateinamen

---

## 🚀 Features

- Multi-JDownloader-Unterstützung (z. B. HomeJD, ServerJD)
- Discord Embeds mit Feldern, Farben, Emojis
- Footer mit Logo
- Docker- und GitHub Actions-kompatibel
- Anpassbares Intervall

---

## ⚙️ Umgebungsvariablen

| Variable         | Beschreibung |
|-----------------|--------------|
| `WEBHOOK_URL`    | Discord Webhook URL für Statusmeldungen |
| `MYJD_EMAIL`     | E-Mail-Adresse deines MyJDownloader-Kontos |
| `MYJD_PASSWORD`  | Passwort deines MyJDownloader-Kontos |
| `MYJD_DEVICES`   | Komma-separierte Liste von Gerät-Namen (`HomeJD,ServerJD`) |
| `INTERVAL`       | Intervall in Sekunden zwischen Statusmeldungen (Standard: 300) |

---

## Screenshot

<img width="420" height="473" alt="image" src="https://github.com/user-attachments/assets/d631db13-0f36-4fac-885b-b616c6833df2" />



---

## 🐳 Docker Beispiel

```bash
docker run -d \
  --name jd-discord-status \
  -e WEBHOOK_URL="https://discord.com/api/webhooks/xxx/yyy" \
  -e MYJD_EMAIL="me@example.com" \
  -e MYJD_PASSWORD="meinpasswort" \
  -e MYJD_DEVICES="HomeJD,ServerJD" \
  -e INTERVAL=600 \
  ghcr.io/kroeberd/jdownloader-discord-monitor:latest
```

---

## 🖥️ Unraid

```xml
<Container>
  <Name>jd-discord-status</Name>
  <Repository>ghcr.io/kroeberd/jdownloader-discord-monitor:latest</Repository>
  <Network>bridge</Network>
  <EnvVars>
    <EnvVar>
      <Key>WEBHOOK_URL</Key>
      <Value>https://discord.com/api/webhooks/xxx/yyy</Value>
    </EnvVar>
    <EnvVar>
      <Key>MYJD_EMAIL</Key>
      <Value>me@example.com</Value>
    </EnvVar>
    <EnvVar>
      <Key>MYJD_PASSWORD</Key>
      <Value>meinpasswort</Value>
    </EnvVar>
    <EnvVar>
      <Key>MYJD_DEVICES</Key>
      <Value>HomeJD,ServerJD</Value>
    </EnvVar>
    <EnvVar>
      <Key>INTERVAL</Key>
      <Value>600</Value>
    </EnvVar>
  </EnvVars>
  <RestartPolicy>unless-stopped</RestartPolicy>
</Container>
```

---

## 🐙 Docker-Compose

```yaml
version: "3.8"
services:
  jd-discord-status:
    image: ghcr.io/kroeberd/jdownloader-discord-monitor:latest
    container_name: jd-discord-status
    environment:
      WEBHOOK_URL: "https://discord.com/api/webhooks/xxx/yyy"
      MYJD_EMAIL: "me@example.com"
      MYJD_PASSWORD: "meinpasswort"
      MYJD_DEVICES: "HomeJD,ServerJD"
      INTERVAL: 600
    restart: unless-stopped
