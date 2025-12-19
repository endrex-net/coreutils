import time

from redis.asyncio import Redis

from coreutils.healthcheck.dto import CheckResult
from coreutils.healthcheck.utils import now_ms, run_with_timeout


class RedisHealthCheck:
    name = "redis"

    def __init__(self, *, redis: Redis, timeout_s: float = 1.0) -> None:
        """
        Тип redis intentionally не аннотируем жестко, чтобы шаблон был переносимым:
        - redis.asyncio.Redis
        - aioredis-подобные клиенты
        главное: await redis.ping()
        """
        self._redis = redis
        self._timeout_s = timeout_s

    async def check(self) -> CheckResult:
        started = time.perf_counter()
        try:

            async def _do() -> None:
                pong = await self._redis.ping()
                # redis-py может вернуть True или b'PONG'/'PONG'
                if not pong:
                    raise RuntimeError("Redis ping returned falsy result")

            await run_with_timeout(_do(), timeout_s=self._timeout_s)
            return CheckResult(ok=True, latency_ms=now_ms(started))
        except Exception as e:  # noqa: BLE001
            return CheckResult(
                ok=False, latency_ms=now_ms(started), error=f"{type(e).__name__}: {e}"
            )
