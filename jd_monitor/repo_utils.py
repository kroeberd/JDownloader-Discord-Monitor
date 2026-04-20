from __future__ import annotations

from datetime import datetime
from typing import TypeVar

from pydantic import BaseModel

from jd_monitor.db import DeviceStateRecord, Document, NotificationRecord, session_scope
from jd_monitor.schemas import AppConfig, DeviceSnapshot, NotificationAttempt

T = TypeVar("T", bound=BaseModel)


def _parse_model(model_type: type[T], payload: str) -> T:
    return model_type.model_validate_json(payload)


class ConfigRepository:
    KEY = "app_config"

    def load(self) -> AppConfig | None:
        with session_scope() as session:
            row = session.get(Document, self.KEY)
            return _parse_model(AppConfig, row.payload) if row else None

    def save(self, config: AppConfig) -> AppConfig:
        payload = config.model_dump_json()
        with session_scope() as session:
            row = session.get(Document, self.KEY)
            if row is None:
                row = Document(key=self.KEY, payload=payload, updated_at=datetime.utcnow())
                session.add(row)
            else:
                row.payload = payload
                row.updated_at = datetime.utcnow()
        return config


class DeviceStateRepository:
    def list(self) -> list[DeviceSnapshot]:
        with session_scope() as session:
            rows = session.query(DeviceStateRecord).all()
            return [_parse_model(DeviceSnapshot, row.payload) for row in rows]

    def get(self, device_id: str) -> DeviceSnapshot | None:
        with session_scope() as session:
            row = session.get(DeviceStateRecord, device_id)
            return _parse_model(DeviceSnapshot, row.payload) if row else None

    def save(self, snapshot: DeviceSnapshot) -> None:
        payload = snapshot.model_dump_json()
        with session_scope() as session:
            row = session.get(DeviceStateRecord, snapshot.device_id)
            if row is None:
                row = DeviceStateRecord(
                    device_id=snapshot.device_id,
                    payload=payload,
                    updated_at=datetime.utcnow(),
                )
                session.add(row)
            else:
                row.payload = payload
                row.updated_at = datetime.utcnow()


class NotificationRepository:
    def list_recent(self, limit: int = 20) -> list[NotificationAttempt]:
        with session_scope() as session:
            rows = (
                session.query(NotificationRecord)
                .order_by(NotificationRecord.created_at.desc())
                .limit(limit)
                .all()
            )
            return [
                NotificationAttempt(
                    webhook_id=row.webhook_id,
                    device_id=row.device_id,
                    event_type=row.event_type,
                    fingerprint=row.fingerprint,
                    delivered=row.delivered,
                    delivered_at=row.created_at,
                    status_code=row.status_code,
                    error_class=row.error_class,
                    error_message=row.error_message,
                )
                for row in rows
            ]

    def was_recently_sent(self, webhook_id: str, device_id: str, fingerprint: str, within_seconds: int) -> bool:
        cutoff = datetime.utcnow().timestamp() - within_seconds
        with session_scope() as session:
            rows = (
                session.query(NotificationRecord)
                .filter(NotificationRecord.webhook_id == webhook_id)
                .filter(NotificationRecord.device_id == device_id)
                .filter(NotificationRecord.fingerprint == fingerprint)
                .order_by(NotificationRecord.created_at.desc())
                .limit(1)
                .all()
            )
            if not rows:
                return False
            return rows[0].created_at.timestamp() >= cutoff

    def save(self, attempt: NotificationAttempt) -> None:
        with session_scope() as session:
            session.add(
                NotificationRecord(
                    webhook_id=attempt.webhook_id,
                    device_id=attempt.device_id,
                    event_type=attempt.event_type,
                    fingerprint=attempt.fingerprint,
                    delivered=attempt.delivered,
                    status_code=attempt.status_code,
                    error_class=attempt.error_class,
                    error_message=attempt.error_message,
                    created_at=attempt.delivered_at,
                )
            )
