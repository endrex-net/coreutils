from unittest.mock import AsyncMock

from coreutils.healthcheck.healthchecks.redis import RedisHealthCheck


async def test_redis_healthcheck_ok_with_true() -> None:
    redis = AsyncMock()
    redis.ping.return_value = True

    check = RedisHealthCheck(redis=redis, timeout_s=0.5)
    res = await check.check()

    assert res.ok is True
    redis.ping.assert_awaited_once()


async def test_redis_healthcheck_ok_with_pong_bytes() -> None:
    redis = AsyncMock()
    redis.ping.return_value = b"PONG"

    check = RedisHealthCheck(redis=redis, timeout_s=0.5)
    res = await check.check()

    assert res.ok is True
    redis.ping.assert_awaited_once()


async def test_redis_healthcheck_fails_on_falsy_ping() -> None:
    redis = AsyncMock()
    redis.ping.return_value = False

    check = RedisHealthCheck(redis=redis, timeout_s=0.5)
    res = await check.check()

    assert res.ok is False
    assert res.error is not None
    assert "Redis ping returned falsy result" in res.error
