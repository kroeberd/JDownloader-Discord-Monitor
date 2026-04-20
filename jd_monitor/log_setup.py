from __future__ import annotations

import json
import logging
from collections import deque
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from jd_monitor.schemas import LogLine


class MemoryLogStore:
    def __init__(self, max_items: int = 300) -> None:
        self._lines: deque[LogLine] = deque(maxlen=max_items)

    def append(self, line: LogLine) -> None:
        self._lines.appendleft(line)

    def recent(self) -> list[LogLine]:
        return list(self._lines)


memory_logs = MemoryLogStore()


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key
            not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
            }
        }
        payload["extra"] = extras
        return json.dumps(payload, ensure_ascii=True)


class MemoryHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        extra = getattr(record, "extra", {})
        memory_logs.append(
            LogLine(
                ts=datetime.utcnow(),
                level=record.levelname,
                logger=record.name,
                message=record.getMessage(),
                extra=extra if isinstance(extra, dict) else {},
            )
        )


def configure_logging(log_path: Path, level: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    formatter = JsonFormatter()
    file_handler = RotatingFileHandler(log_path, maxBytes=2_000_000, backupCount=3)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    memory_handler = MemoryHandler()

    logging.basicConfig(level=level, handlers=[file_handler, stream_handler, memory_handler], force=True)
