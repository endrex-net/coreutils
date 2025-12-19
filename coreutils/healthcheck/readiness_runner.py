import asyncio
from collections.abc import Iterable

from coreutils.healthcheck.dto import CheckResult
from coreutils.healthcheck.interface import HealthCheck


class ReadinessRunner:
    def __init__(
        self,
        *,
        checks: Iterable[HealthCheck],
        timeout_s: float = 2.0,
    ) -> None:
        self._checks = tuple(checks)
        self._timeout_s = timeout_s

    async def run(self) -> dict[str, CheckResult]:
        async def _one(ch: HealthCheck) -> tuple[str, CheckResult]:
            try:
                res = await ch.check()
                return ch.name, res
            except Exception as e:  # noqa: BLE001
                return ch.name, CheckResult(ok=False, error=f"{type(e).__name__}: {e}")

        tasks = [asyncio.create_task(_one(ch)) for ch in self._checks]
        done, pending = await asyncio.wait(tasks, timeout=self._timeout_s)

        for p in pending:
            p.cancel()

        results: dict[str, CheckResult] = {}
        for d in done:
            name, res = await d
            results[name] = res

        for p in pending:
            results.setdefault(
                "_timeout", CheckResult(ok=False, error="Readiness timeout")
            )

        return results
