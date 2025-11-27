from collections.abc import AsyncIterator
from os import environ

import pytest
from redis.asyncio import Redis


@pytest.fixture
def redis_dsn() -> str:
    return environ.get("APP_REDIS_DSN", "redis://127.0.0.1:6379")


@pytest.fixture
async def redis(redis_dsn: str) -> AsyncIterator[Redis]:
    redis = Redis.from_url(redis_dsn)
    await redis.flushall()
    yield redis
    await redis.aclose()
