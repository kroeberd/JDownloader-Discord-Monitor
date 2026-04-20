from __future__ import annotations

import asyncio
from dataclasses import dataclass

from jd_monitor.schemas import DeviceConfig


@dataclass
class ConnectivityProbeResult:
    status: str
    debug_message: str


class ConnectivityService:
    async def probe(self, device: DeviceConfig) -> ConnectivityProbeResult:
        config = device.connectivity
        if not config.enabled or not config.host:
            return ConnectivityProbeResult(
                status="unconfigured",
                debug_message="Direct connectivity probe not configured",
            )

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(config.host, config.port),
                timeout=config.timeout_seconds,
            )
            writer.close()
            await writer.wait_closed()
            del reader
            return ConnectivityProbeResult(
                status="reachable",
                debug_message=f"Direct connectivity probe succeeded for {config.host}:{config.port}",
            )
        except TimeoutError:
            return ConnectivityProbeResult(
                status="unreachable",
                debug_message=f"Direct connectivity probe timed out for {config.host}:{config.port}",
            )
        except OSError as exc:
            return ConnectivityProbeResult(
                status="unreachable",
                debug_message=f"Direct connectivity probe failed for {config.host}:{config.port}: {exc}",
            )
