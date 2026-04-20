from __future__ import annotations

import asyncio
import logging

import httpx

from jd_monitor.repo_utils import NotificationRepository
from jd_monitor.schemas import DeviceSnapshot, NotificationAttempt, NotificationMode, WebhookConfig
from jd_monitor.services.themes import fingerprint_payload, render_payload

logger = logging.getLogger("jd_monitor.notifications")


class NotificationService:
    def __init__(self, repository: NotificationRepository) -> None:
        self.repository = repository
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=10.0))

    async def close(self) -> None:
        await self.client.aclose()

    async def send(
        self,
        webhook: WebhookConfig,
        snapshot: DeviceSnapshot,
        event_type: NotificationMode,
    ) -> NotificationAttempt | None:
        if snapshot.device_id not in webhook.device_ids:
            logger.warning(
                "Skipped notification because device is not assigned to webhook",
                extra={"extra": {"webhook_id": webhook.id, "device_id": snapshot.device_id}},
            )
            return None

        payload = render_payload(webhook, snapshot, event_type)
        fingerprint = fingerprint_payload(payload)
        if self.repository.was_recently_sent(webhook.id, snapshot.device_id, fingerprint, webhook.throttle_seconds):
            logger.info(
                "Suppressed duplicate notification",
                extra={"extra": {"webhook_id": webhook.id, "device_id": snapshot.device_id}},
            )
            return None

        for attempt_number in range(3):
            try:
                response = await self.client.post(str(webhook.url), json=payload)
                if response.status_code == 429 and attempt_number < 2:
                    retry_after = float(response.json().get("retry_after", 1.5))
                    await asyncio.sleep(retry_after)
                    continue
                response.raise_for_status()
                attempt = NotificationAttempt(
                    webhook_id=webhook.id,
                    device_id=snapshot.device_id,
                    event_type=event_type,
                    fingerprint=fingerprint,
                    delivered=True,
                    status_code=response.status_code,
                )
                self.repository.save(attempt)
                return attempt
            except Exception as exc:
                final = attempt_number == 2
                if not final:
                    await asyncio.sleep(1.5 * (attempt_number + 1))
                    continue
                attempt = NotificationAttempt(
                    webhook_id=webhook.id,
                    device_id=snapshot.device_id,
                    event_type=event_type,
                    fingerprint=fingerprint,
                    delivered=False,
                    error_class=type(exc).__name__,
                    error_message=str(exc),
                )
                self.repository.save(attempt)
                logger.error(
                    "Webhook delivery failed",
                    extra={"extra": {"webhook_id": webhook.id, "device_id": snapshot.device_id, "error": str(exc)}},
                )
                return attempt
        return None

    async def send_test(self, webhook: WebhookConfig, snapshot: DeviceSnapshot) -> NotificationAttempt | None:
        return await self.send(webhook, snapshot, "summary")
