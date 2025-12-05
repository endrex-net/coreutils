import abc
import asyncio
import typing
from collections.abc import Awaitable, Callable, Sequence
from functools import wraps
from typing import Concatenate, ParamSpec, TypeVar

import cachetools


P = ParamSpec("P")
RT = TypeVar("RT")


class ICache(typing.Protocol):
    async def get(self, key: str) -> typing.Any: ...

    async def set(
        self, key: str, value: typing.Any, ttl: int | None = None
    ) -> bool | None: ...


class ICached(abc.ABC):
    _cache: ICache


def cached(key_func: Callable[..., str] | None = None, ttl: int = 60 * 60) -> Callable:
    def decorator(
        func: Callable[Concatenate[ICached, P], Awaitable[RT]],
    ) -> Callable[Concatenate[ICached, P], Awaitable[RT]]:
        @wraps(func)
        async def wrapped(self: ICached, *args: P.args, **kwargs: P.kwargs) -> RT:
            key = (
                key_func(*args, **kwargs)
                if key_func
                else f"{self.__class__.__name__}:{func.__name__}:{args}:{kwargs}"
            )

            cached_result = await self._cache.get(key)
            if cached_result is not None:
                return cached_result
            result = await func(self, *args, **kwargs)
            await self._cache.set(key, result, ttl=ttl)
            return result

        return wrapped

    return decorator


class LFUCache:
    def __init__(self, maxsize: int = 1024) -> None:
        self._cache: cachetools.LFUCache = cachetools.LFUCache(maxsize=maxsize)
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> typing.Any:
        async with self._lock:
            return self._cache.get(key)

    async def set(self, key: str, value: typing.Any, ttl: int | None = None) -> bool:
        async with self._lock:
            self._cache[key] = value

        return True


class LRUCache:
    def __init__(self, maxsize: int = 1024):
        self._cache: cachetools.LRUCache = cachetools.LRUCache(maxsize=maxsize)
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> typing.Any:
        async with self._lock:
            return self._cache.get(key)

    async def set(self, key: str, value: typing.Any, ttl: int | None = None) -> bool:
        async with self._lock:
            self._cache[key] = value

        return True


class CombinedCache:
    def __init__(
        self,
        caches: Sequence[ICache],
    ):
        self._caches = caches

    async def get(self, key: str) -> typing.Any:
        missed_caches = []
        for cache in self._caches:
            value = await cache.get(key)

            if value is None:
                missed_caches.append(cache)

            if value is not None:
                for missed_cache in missed_caches:
                    await missed_cache.set(key, value)

                return value

    async def set(
        self, key: str, value: typing.Any, ttl: int | None = None, **kwargs: dict
    ) -> bool | None:
        return all([cache.set(key, value, ttl=ttl) for cache in self._caches])
