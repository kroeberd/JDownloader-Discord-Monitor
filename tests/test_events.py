from jd_monitor.schemas import DeviceSnapshot, TransferTotals
from jd_monitor.services.events import classify_event


def snapshot(active: int, finished: int = 0, status: str = "online") -> DeviceSnapshot:
    return DeviceSnapshot(
        device_id="device-1",
        device_name="Device",
        display_name="Device",
        status=status,
        totals=TransferTotals(active=active, finished=finished, links_total=active + finished),
    )


def test_started_event_when_activity_begins():
    assert classify_event(snapshot(0), snapshot(2)) == "started"


def test_completed_event_when_active_goes_idle():
    assert classify_event(snapshot(3, finished=1), snapshot(0, finished=4)) == "completed"


def test_offline_event_for_offline_status():
    assert classify_event(snapshot(1), snapshot(0, status="offline")) == "offline"
