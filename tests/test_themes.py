from jd_monitor import __version__
from jd_monitor.schemas import BrandingConfig, DeviceSnapshot, ThemeCustomization, TransferTotals, WebhookConfig
from jd_monitor.services.themes import render_payload


def test_payload_hides_empty_optional_fields():
    webhook = WebhookConfig(
        id="wh-1",
        name="Discord",
        url="https://discord.com/api/webhooks/test/test",
        device_ids=["device-1"],
        branding=BrandingConfig(username="Monitor"),
        customization=ThemeCustomization(show_recent_files=False),
    )
    snapshot = DeviceSnapshot(
        device_id="device-1",
        device_name="Box",
        display_name="Box",
        status="online",
        totals=TransferTotals(active=1, links_total=1),
    )
    payload = render_payload(webhook, snapshot, "summary")
    field_names = [field["name"] for field in payload["embeds"][0]["fields"]]
    assert "Recent files" not in field_names


def test_payload_uses_theme_color():
    webhook = WebhookConfig(
        id="wh-1",
        name="Discord",
        url="https://discord.com/api/webhooks/test/test",
        theme="homelab",
    )
    snapshot = DeviceSnapshot(
        device_id="device-1",
        device_name="Box",
        display_name="Box",
        status="online",
        totals=TransferTotals(),
    )
    payload = render_payload(webhook, snapshot, "summary")
    assert payload["embeds"][0]["color"] == 0x3FB950


def test_payload_footer_contains_instance_and_version():
    webhook = WebhookConfig(
        id="wh-1",
        name="Discord",
        url="https://discord.com/api/webhooks/test/test",
        device_ids=["device-1"],
    )
    snapshot = DeviceSnapshot(
        device_id="device-1",
        device_name="Box",
        display_name="Box",
        status="online",
        totals=TransferTotals(),
    )
    payload = render_payload(webhook, snapshot, "summary")
    assert payload["embeds"][0]["footer"]["text"] == f"JD - Monitor . Box . {__version__}"


def test_payload_includes_connectivity_details_when_available():
    webhook = WebhookConfig(
        id="wh-1",
        name="Discord",
        url="https://discord.com/api/webhooks/test/test",
        device_ids=["device-1"],
    )
    snapshot = DeviceSnapshot(
        device_id="device-1",
        device_name="Box",
        display_name="Box",
        status="degraded",
        connectivity_message="Local endpoint reachable",
        totals=TransferTotals(),
    )
    payload = render_payload(webhook, snapshot, "error")
    fields = {field["name"]: field["value"] for field in payload["embeds"][0]["fields"]}
    assert fields["Connectivity"] == "Local endpoint reachable"
