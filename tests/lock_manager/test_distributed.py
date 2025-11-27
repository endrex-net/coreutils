import asyncio

from redis.asyncio import Redis

from coreutils.lock_manager.distributed import DistributedLockManager
from coreutils.lock_manager.interface import AsyncLockManager


async def test_lock_is_exclusive(distributed_lock_manager: AsyncLockManager[str]):
    """
    Два конкурирующих захвата одного и того же key:
    первый успешно входит в критическую секцию, второй — падает по таймауту.
    """
    key = "account-1"
    events: list[str] = []

    async def holder() -> None:
        async with distributed_lock_manager.lock(key, timeout=1.0):
            events.append("holder_acquired")
            # Держим лок, чтобы второй не успел его взять
            await asyncio.sleep(0.1)
            events.append("holder_released")

    async def contender() -> None:
        try:
            async with distributed_lock_manager.lock(key, timeout=0.05):
                events.append("contender_acquired")
        except TimeoutError:
            events.append("contender_timeout")

    task1 = asyncio.create_task(holder())
    # Дадим первому таску шанс захватить лок
    await asyncio.sleep(0.01)
    await contender()
    await task1

    assert "holder_acquired" in events
    assert "holder_released" in events
    assert "contender_timeout" in events
    assert "contender_acquired" not in events


async def test_nested_lock_same_task(distributed_lock_manager: AsyncLockManager[str]):
    """
    Вложенный lock по тому же ключу в одном Task не блокируется повторно,
    но тело внутреннего контекста выполняется.
    """
    key = "nested-key"
    events: list[str] = []

    async with distributed_lock_manager.lock(key, timeout=0.5):
        events.append("outer_enter")
        async with distributed_lock_manager.lock(key, timeout=0.5):
            events.append("inner_enter")

    assert events == ["outer_enter", "inner_enter"]


async def test_cleanup_removes_all_keys(
    distributed_lock_manager: AsyncLockManager[str],
):
    """
    После cleanup() менеджер не должен держать внутренних ключей.
    """
    key1 = "k1"
    key2 = "k2"

    async with distributed_lock_manager.lock(key1, timeout=0.5):
        async with distributed_lock_manager.lock(key2, timeout=0.5):
            keys_inside = set(distributed_lock_manager.get_all_keys())
            assert key1 in keys_inside
            assert key2 in keys_inside

    await distributed_lock_manager.cleanup()
    assert distributed_lock_manager.get_all_keys() == []


async def test_distributed_manager_sets_and_deletes_redis_key(
    distributed_lock_manager: DistributedLockManager[str], redis: Redis
):
    """
    Для DistributedLockManager проверяем, что ключ появляется в Redis
    на время удержания лока и удаляется после.
    """

    key = "redis-key-test"
    redis_key = distributed_lock_manager._get_redis_key(key)  # type: ignore[attr-defined]

    assert await redis.exists(redis_key) == 0

    async with distributed_lock_manager.lock(key, timeout=0.5):
        assert await redis.exists(redis_key) == 1

    # Дадим чуть-чуть времени на удаление (на всякий случай)
    await asyncio.sleep(0.01)
    assert await redis.exists(redis_key) == 0
