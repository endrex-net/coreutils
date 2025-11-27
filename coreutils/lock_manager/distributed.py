import asyncio
import logging
import time
from collections import defaultdict
from collections.abc import AsyncIterator, Hashable, MutableMapping, Sequence
from contextlib import asynccontextmanager
from uuid import uuid4

from redis import WatchError
from redis.asyncio import Redis

from coreutils.lock_manager._utils import get_current_keys


logger = logging.getLogger(__name__)


class DistributedLockManager[LockKey: Hashable]:
    """
    Распределённый менеджер локов поверх Redis.

    Особенности:
    - Лок распространяется на все инстансы приложения (общий Redis).
    - asyncio.Lock на каждый ключ, чтобы не гонять лишний трафик в Redis.
    - Вложенные вызовы lock(...) в рамках одного asyncio.Task по тому же key
      не лочатся: просто логируется warning и выполняется тело контекстного менеджера.
    """

    def __init__(
        self,
        redis: Redis,
        *,
        ttl_ms: int = 10_000,
        retry_interval: float = 0.1,
        namespace: str = "lock",
    ) -> None:
        """
        :param redis: redis.asyncio.Redis клиент
        :param ttl_ms: TTL ключа в Redis в миллисекундах
        :param retry_interval: задержка между попытками захвата лока (секунды)
        :param namespace: префикс для всех ключей в Redis
        """
        self._redis = redis
        self._ttl_ms = ttl_ms
        self._retry_interval = retry_interval
        self._namespace = namespace

        # redis_key -> value (уникальный идентификатор владельца лока)
        self._active_locks: MutableMapping[str, str] = {}

        # локи на уровне инстанса, один asyncio.Lock на ключ
        self._local_locks: MutableMapping[LockKey, asyncio.Lock] = defaultdict(
            asyncio.Lock
        )

    # --- публичный API, соответствующий AsyncLockManager ---

    @asynccontextmanager
    async def lock(
        self,
        key: LockKey,
        *,
        timeout: float = 5.0,
    ) -> AsyncIterator[None]:
        """
        Захватить лок по ключу с общим таймаутом:
        - сначала ждём локальный asyncio.Lock (внутри процесса),
        - затем ждём Redis-лок.
        Если суммарно не укладываемся в timeout, кидаем TimeoutError.
        """
        if asyncio.current_task() is None:
            raise RuntimeError("lock() must be called from within an asyncio task")

        task_keys = get_current_keys()

        # re-entrant для того же key в рамках одного Task
        if key in task_keys:
            logger.warning(
                "Nested lock for the same key %r in the same task; "
                "body will execute without acquiring lock again.",
                key,
            )
            # вообще не трогаем локи / Redis, просто выполняем тело
            yield
            return

        redis_key = self._get_redis_key(key)
        value = str(uuid4())
        local_lock = self._local_locks[key]

        start = time.monotonic()
        acquired_redis = False

        # 1. Ждём локальный lock с таймаутом
        try:
            try:
                await asyncio.wait_for(local_lock.acquire(), timeout=timeout)
            except TimeoutError as exc:
                raise TimeoutError(
                    f"Could not acquire local lock for key: {key!r}"
                ) from exc

            task_keys.add(key)

            # 2. Считаем оставшийся таймаут для Redis
            elapsed = time.monotonic() - start
            remaining = timeout - elapsed

            if remaining <= 0:
                # Время ушло целиком на ожидание локального лока
                raise TimeoutError(
                    f"Timeout while acquiring lock for key: {key!r} "
                    "(no time left for Redis)"
                )

            # 3. Пытаемся захватить Redis-лок в оставшееся время
            acquired_redis = await self._acquire(
                redis_key,
                value,
                timeout=remaining,
            )
            if not acquired_redis:
                raise TimeoutError(f"Could not acquire Redis lock for key: {key!r}")

            self._active_locks[redis_key] = value

            try:
                # 4. Критическая секция
                yield
            finally:
                if acquired_redis:
                    await self.remove_lock(key)
        finally:
            task_keys.discard(key)
            # ВАЖНО: отпускаем локальный lock, если он всё ещё удерживается
            if local_lock.locked():
                local_lock.release()

    async def remove_lock(self, key: LockKey) -> None:
        redis_key = self._get_redis_key(key)
        if redis_key not in self._active_locks:
            # Лока у этого инстанса уже нет
            self._cleanup_local_lock(key)
            return

        value = self._active_locks.pop(redis_key)
        await self._release(redis_key, value)
        self._cleanup_local_lock(key)

    async def cleanup(self) -> None:
        """
        Снять все локи, которые этот инстанс считает своими.

        Обычно вызывается при graceful shutdown.
        """
        keys = list(self.get_all_keys())
        for key in keys:
            await self.remove_lock(key)

    def get_all_keys(self) -> Sequence[LockKey]:
        return list(self._local_locks.keys())

    # --- внутренняя работа с Redis ---

    async def _acquire(
        self,
        redis_key: str,
        value: str,
        *,
        timeout: float = 5.0,
    ) -> bool:
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            ok = await self._redis.set(
                redis_key,
                value,
                nx=True,
                px=self._ttl_ms,
            )
            if ok:
                return True

            await asyncio.sleep(self._retry_interval)

        return False

    async def _release(self, redis_key: str, value: str) -> bool:
        """
        Безопасное удаление лока:
        удаляем только если значение совпадает с нашим.
        """
        async with self._redis.pipeline() as pipe:
            while True:
                try:
                    await pipe.watch(redis_key)
                    current_value: bytes | None = await self._redis.get(redis_key)
                    if current_value is None or current_value.decode() != value:
                        # Лок уже чей-то другой или его нет
                        await pipe.reset()
                        return False

                    pipe.multi()
                    pipe.delete(redis_key)
                    await pipe.execute()
                    break
                except WatchError:
                    # Кто-то другой модифицировал ключ — пробуем ещё раз
                    continue
                finally:
                    await pipe.reset()

        return True

    # --- утилиты ---

    def _get_redis_key(self, key: LockKey) -> str:
        return f"{self._namespace}:{key}"

    def _cleanup_local_lock(self, key: LockKey) -> None:
        lock = self._local_locks.get(key)
        if lock is not None and not lock.locked():
            # Если никто не ждёт этот лок, можно убрать его из словаря
            del self._local_locks[key]
