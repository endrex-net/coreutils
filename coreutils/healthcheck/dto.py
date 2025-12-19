from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True, kw_only=True)
class CheckResult:
    ok: bool
    latency_ms: int | None = None
    error: str | None = None


@dataclass(slots=True)
class LivenessDto:
    ok: bool
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "message": self.message}


@dataclass(slots=True)
class CheckDto:
    ok: bool
    latency_ms: int | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"ok": self.ok}
        # latency_ms/error удобно опускать, если None (чтобы ответ был чище)
        if self.latency_ms is not None:
            data["latency_ms"] = self.latency_ms
        if self.error is not None:
            data["error"] = self.error
        return data


@dataclass(slots=True)
class ReadinessDto:
    ok: bool
    checks: dict[str, CheckDto]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "checks": {name: check.to_dict() for name, check in self.checks.items()},
        }
