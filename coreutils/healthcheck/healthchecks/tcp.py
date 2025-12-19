import asyncio
import time

from coreutils.healthcheck.dto import CheckResult
from coreutils.healthcheck.utils import now_ms, run_with_timeout


class TcpConnectHealthCheck:
    """
    Универсальная проверка для SMTP и похожих зависимостей:
    достаточно TCP connect (быстро и без сторонних библиотек).
    """

    def __init__(
        self, *, name: str, host: str, port: int, timeout_s: float = 1.0
    ) -> None:
        self.name = name
        self._host = host
        self._port = port
        self._timeout_s = timeout_s

    async def check(self) -> CheckResult:
        started = time.perf_counter()
        try:

            async def _do() -> None:
                reader, writer = await asyncio.open_connection(self._host, self._port)
                writer.close()
                await writer.wait_closed()

            await run_with_timeout(_do(), timeout_s=self._timeout_s)
            return CheckResult(ok=True, latency_ms=now_ms(started))
        except Exception as e:  # noqa: BLE001
            return CheckResult(
                ok=False, latency_ms=now_ms(started), error=f"{type(e).__name__}: {e}"
            )
