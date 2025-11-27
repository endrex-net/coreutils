import asyncio
import logging
from collections import defaultdict
from collections.abc import AsyncIterator, Hashable, MutableMapping, Sequence
from contextlib import asynccontextmanager

from coreutils.lock_manager._utils import get_current_keys


logger = logging.getLogger(__name__)


class InMemoryLockManager[LockKey: Hashable]:
    """
    In-memory менеджер локов.

    Не распределённый: работает только внутри одного инстанса.
    Семантика такая же, как у DistributedLockManager:
    - взаимное исключение по ключу;
    - re-entrant по тому же key внутри одного Task;
    - таймаут на захват лока.
    """

    def __init__(self) -> None:
        # Один asyncio.Lock на ключ
        self._local_locks: MutableMapping[LockKey, asyncio.Lock] = defaultdict(
            asyncio.Lock
        )

    @asynccontextmanager
    async def lock(
        self,
        key: LockKey,
        *,
        timeout: float = 5.0,
    ) -> AsyncIterator[None]:
        if asyncio.current_task() is None:
            raise RuntimeError("lock() must be called from within an asyncio task")

        task_keys = get_current_keys()

        # re-entrant для того же key в рамках одного Task
        if key in task_keys:
            logger.warning(
                "Nested in-memory lock for the same key %r in the same task; "
                "body will execute without acquiring lock again.",
                key,
            )
            yield
            return

        local_lock = self._local_locks[key]

        # Таймаут реализуем через asyncio.wait_for
        try:
            await asyncio.wait_for(local_lock.acquire(), timeout=timeout)
        except TimeoutError as exc:
            raise TimeoutError(
                f"Could not acquire in-memory lock for key: {key!r}"
            ) from exc

        task_keys.add(key)
        try:
            try:
                yield
            finally:
                local_lock.release()
        finally:
            task_keys.discard(key)
            # Лок не удаляем из словаря, чтобы не ломать ожидающие его таски

    async def remove_lock(self, key: LockKey) -> None:
        """
        Для InMemory-реализации remove_lock почти не нужен, но оставим
        для единообразия интерфейса.

        Здесь мы пытаемся отпустить лок, если он ещё захвачен в текущем инстансе.
        """
        lock = self._local_locks.get(key)
        if lock is None:
            return

        if lock.locked():
            lock.release()

    async def cleanup(self) -> None:
        """
        Снять все локи, которые этот инстанс считает своими.
        """
        for key, lock in list(self._local_locks.items()):
            if lock.locked():
                lock.release()
        self._local_locks.clear()

    def get_all_keys(self) -> Sequence[LockKey]:
        return list(self._local_locks.keys())
