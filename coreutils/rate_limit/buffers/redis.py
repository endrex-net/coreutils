from collections.abc import Callable

from redis.asyncio import Redis

from coreutils.rate_limit.buffers.base import IBuffer


class RedisBuffer[T](IBuffer[T]):
    def __init__(
        self,
        redis: Redis,
        key: str,
        capacity: int,
        serializer: Callable[[T], str] = lambda x: str(x),
        deserializer: Callable[[str], T] = lambda x: x,
    ) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be > 0")

        self._redis = redis
        self._key = key
        self._capacity = capacity
        self._serializer = serializer
        self._deserializer = deserializer

    async def put(self, item: T) -> None:
        value = self._serializer(item)
        async with self._redis.pipeline(transaction=True) as pipe:
            await pipe.rpush(self._key, value)
            await pipe.ltrim(self._key, -self._capacity, -1)
            await pipe.execute()

    async def capacity(self) -> int:
        return await self._redis.llen(self._key)

    async def get(self) -> T:
        value = await self._redis.lpop(self._key)
        if value is None:
            raise ValueError("buffer is empty")
        return self._deserializer(value)
