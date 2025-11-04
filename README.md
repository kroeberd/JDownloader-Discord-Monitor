# ![J[Downloader Logo](# !](https://raw.githubusercontent.com/kroeberd/JDownloader-Discord-Monitor/refs/heads/main/logos/logo_big_JM_400_300.jpg) 
 # JDownloader-Docker-Monitor

[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/kroeberd/JDownloader-Discord-Monitor/docker.yml?branch=main)](https://github.com/kroeberd/JDownloader-Discord-Monitor/actions)  
[![License: GPL-3.0](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://opensource.org/licenses/GPL-3.0)  
[![Docker Pulls](https://img.shields.io/docker/pulls/kroeberd/jdownloader-discord-monitor)](https://hub.docker.com/r/kroeberd/jdownloader-docker-monitor)  

**JDownloader-Docker-Monitor** monitors one or more JDownloader instances via **MyJDownloader** and sends periodic **Discord updates** as rich embeds.

> ⚠️ *Beta version – use at your own risk.*

![Example Embed](screenshot.png) <!-- Replace with your screenshot -->

---

## 🌟 Features

- ✅ Monitor multiple JDownloader devices simultaneously  
- ✅ Display active downloads, progress, speed, and filenames  
- ✅ Discord embeds with colors, emojis, and footer logo  
- ✅ Configurable interval between updates  
- ✅ Automatic hiding of unavailable fields  
- ✅ Works with Docker, Docker Compose, and Unraid
- ✅ Multilingual, english or german

---

## 📊 Status Messages

Each Discord embed may include:

| Field | Description |
|-------|-------------|
| 📥 Active downloads | Number of ongoing downloads |
| ⚡ Speed | Current download speed |
| ⏱️ Progress | Percentage completed |
| 💾 Data | Downloaded / Total size in GB |
| 🖥️ Device info | JDownloader version and platform |
| 🗂️ Filenames | Up to 5 filenames in the queue |

---

## ⚙️ Environment Variables

| Variable       | Description |
|----------------|-------------|
| `WEBHOOK_URL`  | Discord webhook URL for status messages |
| `MYJD_EMAIL`    | Email of your MyJDownloader account |
| `MYJD_PASSWORD` | Password for your MyJDownloader account |
| `MYJD_DEVICES`  | Comma-separated device names (e.g., `HomeJD,ServerJD`) |
| `INTERVAL`      | Interval in seconds between updates (default: `300`) |
| `LANG`      | `en` for englisch, `de` for german  |


---

## 🐳 Docker

### Run with Docker

```bash
docker run -d \
  --name JDownloader-Docker-Monitor \
  -e WEBHOOK_URL="https://discord.com/api/webhooks/xxx/yyy" \
  -e MYJD_EMAIL="me@example.com" \
  -e MYJD_PASSWORD="myPassword" \
  -e MYJD_DEVICES="HomeJD,ServerJD" \
  -e INTERVAL=600 \
  -e LANG=en \
  ghcr.io/kroeberd/jdownloader-discord-monitor:latest
```

---

## 🖥️ Unraid
Example Unraid container configuration:
```xml
<Container>
  <Name>JDownloader-Docker-Monitor</Name>
  <Repository>ghcr.io/kroeberd/jdownloader-discord-monitor:latest</Repository>
  <Network>bridge</Network>
  <EnvVars>
    <EnvVar><Key>WEBHOOK_URL</Key><Value>https://discord.com/api/webhooks/xxx/yyy</Value></EnvVar>
    <EnvVar><Key>MYJD_EMAIL</Key><Value>me@example.com</Value></EnvVar>
    <EnvVar><Key>MYJD_PASSWORD</Key><Value>myPassword</Value></EnvVar>
    <EnvVar><Key>MYJD_DEVICES</Key><Value>HomeJD,ServerJD</Value></EnvVar>
    <EnvVar><Key>INTERVAL</Key><Value>600</Value></EnvVar>
    <EnvVar><Key>LANG</Key><Value>en</Value></EnvVar>
  </EnvVars>
  <RestartPolicy>unless-stopped</RestartPolicy>
</Container>

```

---

## 🐙 Docker-Compose

```yaml
version: "3.8"
services:
  JDownloader-Docker-Monitor:
    image: ghcr.io/kroeberd/jdownloader-discord-monitor:latest
    container_name: JDownloader-Docker-Monitor
    environment:
      WEBHOOK_URL: "https://discord.com/api/webhooks/xxx/yyy"
      MYJD_EMAIL: "me@example.com"
      MYJD_PASSWORD: "myPassword"
      MYJD_DEVICES: "HomeJD,ServerJD"
      INTERVAL: 600
      LANG: en
    restart: unless-stopped
