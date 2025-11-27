from collections.abc import AsyncIterator, Hashable, Sequence
from contextlib import asynccontextmanager
from typing import Protocol


class AsyncLockManager[LockKey: Hashable](Protocol):
    """Протокол для асинхронного менеджера распределённых локов."""

    @asynccontextmanager  # type: ignore[arg-type]
    async def lock(self, key: LockKey, *, timeout: float = 5.0) -> AsyncIterator[None]:
        """
        Захватить лок по ключу `key` с таймаутом `timeout` (в секундах).

        Если лок не удаётся взять за отведённое время, должен бросить TimeoutError.
        """
        ...

    async def remove_lock(self, key: LockKey) -> None:
        """Снять лок по ключу, если он активен в текущем инстансе."""
        ...

    async def cleanup(self) -> None:
        """Снять все активные локи в текущем инстансе (используется при shutdown)."""
        ...

    def get_all_keys(self) -> Sequence[LockKey]:
        """Вернуть все ключи, по которым в этом инстансе есть локи."""
        ...
