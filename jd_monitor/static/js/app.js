const state = {
  config: null,
  themes: window.__THEMES__ || [],
  devices: [],
  audit: [],
  logs: [],
};

const sections = document.querySelectorAll(".panel");
const navItems = document.querySelectorAll(".nav-item");

navItems.forEach((button) => {
  button.addEventListener("click", () => {
    navItems.forEach((item) => item.classList.remove("active"));
    sections.forEach((section) => section.classList.remove("active"));
    button.classList.add("active");
    document.getElementById(button.dataset.section).classList.add("active");
  });
});

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `Request failed: ${response.status}`);
  }
  return response.json();
}

function toast(message) {
  const node = document.createElement("div");
  node.className = "toast";
  node.textContent = message;
  document.body.appendChild(node);
  setTimeout(() => node.remove(), 2600);
}

function metricCards() {
  const online = state.devices.filter((item) => item.status === "online").length;
  const active = state.devices.reduce((sum, item) => sum + (item.totals?.active || 0), 0);
  const hooks = state.config.webhooks.length;
  const metrics = [
    ["Devices online", online],
    ["Active downloads", active],
    ["Webhooks", hooks],
    ["Themes", state.themes.length],
  ];
  document.getElementById("metric-cards").innerHTML = metrics
    .map(([label, value]) => `<div class="metric-card"><span>${label}</span><strong>${value}</strong></div>`)
    .join("");
}

function renderDashboard() {
  metricCards();
  const badge = document.getElementById("health-badge");
  badge.textContent = state.health.message;
  badge.className = `badge ${state.health.status}`;
  document.getElementById("device-cards").innerHTML = state.devices
    .map((device) => `
      <div class="device-card">
        <div class="card-header">
          <h3>${device.display_name}</h3>
          <span class="badge ${device.status === "online" ? "ok" : device.status === "offline" ? "error" : "degraded"}">${device.status}</span>
        </div>
        <div class="editor-grid">
          <div><span class="device-meta">Speed</span><strong>${(device.totals.speed_bytes_per_second / 1024 / 1024).toFixed(2)} MB/s</strong></div>
          <div><span class="device-meta">Progress</span><strong>${device.totals.progress_percent.toFixed(1)}%</strong></div>
          <div><span class="device-meta">Active</span><strong>${device.totals.active}</strong></div>
          <div><span class="device-meta">Queue</span><strong>${device.totals.links_total}</strong></div>
        </div>
      </div>
    `)
    .join("") || "<div class='device-card'>No device data yet. Save credentials and trigger a poll.</div>";

  document.getElementById("audit-list").innerHTML = state.audit
    .map((item) => `
      <div class="audit-item">
        <strong>${item.event_type} · ${item.device_id}</strong>
        <div class="log-meta">${item.webhook_id} · ${item.delivered ? "delivered" : "failed"}</div>
      </div>
    `)
    .join("") || "<div class='audit-item'>No notifications recorded yet.</div>";
}

function renderSettings() {
  document.getElementById("credentials-email").value = state.config.credentials.email || "";
  document.getElementById("credentials-password").value = state.config.credentials.password || "";
  document.getElementById("locale").value = state.config.locale;
  document.getElementById("timezone").value = state.config.timezone;
}

function deviceCard(device, index) {
  const options = state.config.webhooks
    .map((webhook) => `<option value="${webhook.id}" ${device.webhook_ids.includes(webhook.id) ? "selected" : ""}>${webhook.name}</option>`)
    .join("");
  return `
    <div class="editor-card" data-device="${index}">
      <div class="editor-grid">
        <label>ID <input data-key="id" value="${device.id}"></label>
        <label>MyJD device name <input data-key="name" value="${device.name}"></label>
        <label>Display name <input data-key="display_name" value="${device.display_name || ""}"></label>
        <label>Poll interval (s) <input data-key="poll_interval_seconds" type="number" value="${device.poll_interval_seconds}"></label>
        <label>Summary interval (min) <input data-key="summary_interval_minutes" type="number" value="${device.summary_interval_minutes}"></label>
        <label>Webhooks <select data-key="webhook_ids" multiple>${options}</select></label>
      </div>
      <label class="checkbox-row"><input data-key="enabled" type="checkbox" ${device.enabled ? "checked" : ""}>Enabled</label>
    </div>
  `;
}

function webhookCard(webhook, index) {
  const deviceOptions = state.config.devices
    .map((device) => `<option value="${device.id}" ${webhook.device_ids.includes(device.id) ? "selected" : ""}>${device.display_name || device.name}</option>`)
    .join("");
  const themeOptions = state.themes
    .map((theme) => `<option value="${theme.id}" ${webhook.theme === theme.id ? "selected" : ""}>${theme.label}</option>`)
    .join("");
  return `
    <div class="editor-card" data-webhook="${index}">
      <div class="editor-grid">
        <label>ID <input data-key="id" value="${webhook.id}"></label>
        <label>Name <input data-key="name" value="${webhook.name}"></label>
        <label>Webhook URL <input data-key="url" value="${webhook.url}"></label>
        <label>Theme <select data-key="theme">${themeOptions}</select></label>
        <label>Locale <select data-key="locale"><option value="en" ${webhook.locale === "en" ? "selected" : ""}>English</option><option value="de" ${webhook.locale === "de" ? "selected" : ""}>Deutsch</option></select></label>
        <label>Throttle (s) <input data-key="throttle_seconds" type="number" value="${webhook.throttle_seconds}"></label>
        <label>Devices <select data-key="device_ids" multiple>${deviceOptions}</select></label>
        <label>Sender name <input data-key="branding.username" value="${webhook.branding.username}"></label>
      </div>
      <label class="checkbox-row"><input data-key="enabled" type="checkbox" ${webhook.enabled ? "checked" : ""}>Enabled</label>
    </div>
  `;
}

function renderEditors() {
  document.getElementById("devices-editor").innerHTML = state.config.devices.map(deviceCard).join("");
  document.getElementById("webhooks-editor").innerHTML = state.config.webhooks.map(webhookCard).join("");
  const previewSelect = document.getElementById("preview-webhook");
  previewSelect.innerHTML = state.config.webhooks
    .map((webhook) => `<option value="${webhook.id}">${webhook.name}</option>`)
    .join("");
}

function renderLogs() {
  document.getElementById("log-lines").innerHTML = state.logs
    .map((line) => `<div class="log-item"><strong>${line.level}</strong><div>${line.message}</div><div class="log-meta">${line.logger}</div></div>`)
    .join("") || "<div class='log-item'>No logs captured yet.</div>";
}

function collectEditors() {
  state.config.devices = Array.from(document.querySelectorAll("[data-device]")).map((card) => ({
    id: card.querySelector("[data-key='id']").value,
    name: card.querySelector("[data-key='name']").value,
    display_name: card.querySelector("[data-key='display_name']").value || null,
    enabled: card.querySelector("[data-key='enabled']").checked,
    poll_interval_seconds: Number(card.querySelector("[data-key='poll_interval_seconds']").value),
    summary_interval_minutes: Number(card.querySelector("[data-key='summary_interval_minutes']").value),
    webhook_ids: Array.from(card.querySelector("[data-key='webhook_ids']").selectedOptions).map((opt) => opt.value),
    quiet_hours: { enabled: false, start: "23:00", end: "07:00", timezone: state.config.timezone },
  }));

  state.config.webhooks = Array.from(document.querySelectorAll("[data-webhook]")).map((card) => ({
    id: card.querySelector("[data-key='id']").value,
    name: card.querySelector("[data-key='name']").value,
    url: card.querySelector("[data-key='url']").value,
    enabled: card.querySelector("[data-key='enabled']").checked,
    theme: card.querySelector("[data-key='theme']").value,
    locale: card.querySelector("[data-key='locale']").value,
    throttle_seconds: Number(card.querySelector("[data-key='throttle_seconds']").value),
    device_ids: Array.from(card.querySelector("[data-key='device_ids']").selectedOptions).map((opt) => opt.value),
    branding: { username: card.querySelector("[data-key='branding.username']").value, avatar_url: null },
    customization: {
      accent_color: "#58a6ff",
      accent_icon: "satellite",
      compact: false,
      verbose: true,
      show_device_details: true,
      show_transfer_stats: true,
      show_recent_files: true,
      show_connection_badge: true,
    },
    notification_modes: ["summary", "started", "completed", "offline"],
  }));

  state.config.credentials.email = document.getElementById("credentials-email").value;
  state.config.credentials.password = document.getElementById("credentials-password").value;
  state.config.locale = document.getElementById("locale").value;
  state.config.timezone = document.getElementById("timezone").value;
}

async function refreshPreview() {
  collectEditors();
  const webhookId = document.getElementById("preview-webhook").value;
  const webhook = state.config.webhooks.find((item) => item.id === webhookId) || state.config.webhooks[0];
  if (!webhook) {
    toast("Create a webhook first.");
    return;
  }
  const result = await api("/api/preview", {
    method: "POST",
    body: JSON.stringify({ webhook, event_type: document.getElementById("preview-event").value }),
  });
  document.getElementById("preview-json").textContent = JSON.stringify(result.payload, null, 2);
  document.getElementById("preview-html").innerHTML = result.html;
}

async function bootstrap() {
  const result = await api("/api/bootstrap");
  state.config = result.config;
  state.devices = result.devices;
  state.audit = result.last_audit_events;
  state.health = result.health;
  state.themes = result.themes;
  state.logs = await api("/api/logs");
  renderDashboard();
  renderSettings();
  renderEditors();
  renderLogs();
  refreshPreview();
}

document.getElementById("add-device").addEventListener("click", () => {
  state.config.devices.push({
    id: `device-${Date.now()}`,
    name: "",
    display_name: "",
    enabled: true,
    poll_interval_seconds: 300,
    summary_interval_minutes: 30,
    webhook_ids: [],
    quiet_hours: { enabled: false, start: "23:00", end: "07:00", timezone: state.config.timezone },
  });
  renderEditors();
});

document.getElementById("add-webhook").addEventListener("click", () => {
  state.config.webhooks.push({
    id: `webhook-${Date.now()}`,
    name: "New webhook",
    url: "",
    enabled: true,
    device_ids: [],
    theme: "modern",
    locale: state.config.locale,
    branding: { username: "JDownloader Monitor", avatar_url: null },
    customization: {
      accent_color: "#58a6ff",
      accent_icon: "satellite",
      compact: false,
      verbose: true,
      show_device_details: true,
      show_transfer_stats: true,
      show_recent_files: true,
      show_connection_badge: true,
    },
    notification_modes: ["summary"],
    throttle_seconds: 180,
  });
  renderEditors();
});

document.getElementById("save-config").addEventListener("click", async () => {
  collectEditors();
  await api("/api/config", { method: "PUT", body: JSON.stringify(state.config) });
  toast("Configuration saved");
  await bootstrap();
});

document.getElementById("run-now").addEventListener("click", async () => {
  await api("/api/poller/run-now", { method: "POST" });
  toast("Poll requested");
});

document.getElementById("refresh-preview").addEventListener("click", refreshPreview);

document.getElementById("test-webhook").addEventListener("click", async () => {
  collectEditors();
  const webhookId = document.getElementById("preview-webhook").value;
  const webhook = state.config.webhooks.find((item) => item.id === webhookId);
  if (!webhook) {
    return;
  }
  const result = await api("/api/webhooks/test", {
    method: "POST",
    body: JSON.stringify({ webhook }),
  });
  toast(result.ok ? "Test notification sent" : "Test notification failed");
});

bootstrap().catch((error) => {
  console.error(error);
  toast(error.message);
});
