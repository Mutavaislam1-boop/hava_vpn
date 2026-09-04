from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RuntimeDiagnostics:
    bot_id: int | None = None
    bot_username: str | None = None
    backend_ready: bool = False
    database_ready: bool = False


runtime = RuntimeDiagnostics()
