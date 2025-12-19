import time

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from coreutils.healthcheck.dto import CheckResult
from coreutils.healthcheck.utils import now_ms, run_with_timeout


class PostgresHealthCheck:
    name = "postgres"

    def __init__(self, *, engine: AsyncEngine, timeout_s: float = 1.0) -> None:
        self._engine = engine
        self._timeout_s = timeout_s

    async def check(self) -> CheckResult:
        started = time.perf_counter()
        try:

            async def _do() -> None:
                async with self._engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))

            await run_with_timeout(_do(), timeout_s=self._timeout_s)
            return CheckResult(ok=True, latency_ms=now_ms(started))
        except Exception as e:  # noqa: BLE001
            return CheckResult(
                ok=False, latency_ms=now_ms(started), error=f"{type(e).__name__}: {e}"
            )
