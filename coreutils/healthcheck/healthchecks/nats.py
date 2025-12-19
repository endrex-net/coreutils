import time

from faststream.nats import NatsBroker

from coreutils.healthcheck.dto import CheckResult
from coreutils.healthcheck.utils import now_ms, run_with_timeout


class NatsHealthCheck:
    name = "nats"

    def __init__(self, *, broker: NatsBroker, timeout_s: float = 1.0) -> None:
        self._broker = broker
        self._timeout_s = timeout_s

    async def check(self) -> CheckResult:
        started = time.perf_counter()
        try:

            async def _do() -> None:
                await self._broker.ping(self._timeout_s)

            await run_with_timeout(_do(), timeout_s=self._timeout_s)
            return CheckResult(ok=True, latency_ms=now_ms(started))
        except Exception as e:  # noqa: BLE001
            return CheckResult(
                ok=False, latency_ms=now_ms(started), error=f"{type(e).__name__}: {e}"
            )
