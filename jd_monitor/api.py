from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from jd_monitor.schemas import AppConfig, DashboardSummary, PreviewRequest, PreviewResponse, TestWebhookRequest
from jd_monitor.services.defaults import default_config_from_env
from jd_monitor.services.themes import available_themes, render_preview

templates = Jinja2Templates(directory="jd_monitor/templates")
router = APIRouter()


def services(request: Request):
    return request.app.state.services


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {"request": request, "title": "JDownloader Monitor", "themes": available_themes()},
    )


@router.get("/api/bootstrap", response_model=DashboardSummary)
async def bootstrap(svc=Depends(services)):
    config = svc.config_repo.load() or default_config_from_env()
    return DashboardSummary(
        health=svc.poller.health,
        config=config,
        devices=svc.device_repo.list(),
        last_audit_events=svc.notification_repo.list_recent(),
        themes=available_themes(),
    )


@router.get("/api/config", response_model=AppConfig)
async def get_config(svc=Depends(services)):
    return svc.config_repo.load() or default_config_from_env()


@router.put("/api/config", response_model=AppConfig)
async def save_config(config: AppConfig, svc=Depends(services)):
    saved = svc.config_repo.save(config)
    await svc.poller.trigger_now()
    return saved


@router.get("/api/devices")
async def get_devices(svc=Depends(services)):
    return svc.device_repo.list()


@router.get("/api/logs")
async def get_logs(svc=Depends(services)):
    return svc.logs.recent()


@router.get("/api/audit")
async def get_audit(svc=Depends(services)):
    return svc.notification_repo.list_recent(50)


@router.get("/api/themes")
async def get_themes():
    return available_themes()


@router.post("/api/preview", response_model=PreviewResponse)
async def preview(payload: PreviewRequest, svc=Depends(services)):
    snapshot = payload.snapshot or svc.sample_snapshot()
    return render_preview(payload.webhook, snapshot, payload.event_type)


@router.post("/api/webhooks/test")
async def send_test(payload: TestWebhookRequest, svc=Depends(services)):
    snapshot = payload.snapshot or svc.sample_snapshot()
    attempt = await svc.notifications.send_test(payload.webhook, snapshot)
    return {"ok": attempt.delivered if attempt else False, "attempt": attempt}


@router.post("/api/poller/run-now")
async def poll_now(svc=Depends(services)):
    await svc.poller.trigger_now()
    return {"ok": True}


@router.get("/health/live")
async def health_live():
    return {"status": "ok"}


@router.get("/health/ready")
async def health_ready(svc=Depends(services)):
    return svc.poller.health
