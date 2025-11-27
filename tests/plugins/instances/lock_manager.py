import pytest
from redis.asyncio import Redis

from coreutils.lock_manager.distributed import DistributedLockManager
from coreutils.lock_manager.in_memory import InMemoryLockManager
from coreutils.lock_manager.interface import AsyncLockManager


@pytest.fixture
def distributed_lock_manager(redis: Redis) -> AsyncLockManager[str]:
    return DistributedLockManager[str](
        redis,
        ttl_ms=1_000,
        retry_interval=0.01,
        namespace="test_lock",
    )


@pytest.fixture
def in_memory_lock_manager() -> AsyncLockManager[str]:
    return InMemoryLockManager[str]()
