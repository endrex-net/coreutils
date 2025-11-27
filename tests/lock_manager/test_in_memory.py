import asyncio

from coreutils.lock_manager.interface import AsyncLockManager


async def test_lock_is_exclusive(in_memory_lock_manager: AsyncLockManager[str]):
    key = "account-1"
    events: list[str] = []

    async def holder() -> None:
        async with in_memory_lock_manager.lock(key, timeout=1.0):
            events.append("holder_acquired")
            # Держим лок, чтобы второй не успел его взять
            await asyncio.sleep(0.1)
            events.append("holder_released")

    async def contender() -> None:
        try:
            async with in_memory_lock_manager.lock(key, timeout=0.05):
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


async def test_nested_lock_same_task(in_memory_lock_manager: AsyncLockManager[str]):
    key = "nested-key"
    events: list[str] = []

    async with in_memory_lock_manager.lock(key, timeout=0.5):
        events.append("outer_enter")
        async with in_memory_lock_manager.lock(key, timeout=0.5):
            events.append("inner_enter")

    assert events == ["outer_enter", "inner_enter"]


async def test_cleanup_removes_all_keys(in_memory_lock_manager: AsyncLockManager[str]):
    key1 = "k1"
    key2 = "k2"

    async with in_memory_lock_manager.lock(key1, timeout=0.5):
        async with in_memory_lock_manager.lock(key2, timeout=0.5):
            keys_inside = set(in_memory_lock_manager.get_all_keys())
            assert key1 in keys_inside
            assert key2 in keys_inside

    await in_memory_lock_manager.cleanup()
    assert in_memory_lock_manager.get_all_keys() == []
