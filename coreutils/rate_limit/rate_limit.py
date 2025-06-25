import asyncio
import logging
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime, timedelta
from functools import wraps
from typing import Any, ParamSpec

from coreutils.rate_limit.buffers import IBuffer, MemoryBuffer


logger = logging.getLogger(__name__)

P = ParamSpec("P")


def rate_limit[T](
    max_calls: int,
    per_seconds: int,
    buffer: IBuffer[datetime] | None = None,
) -> Callable[
    [Callable[P, Coroutine[Any, Any, T]]], Callable[P, Coroutine[Any, Any, T]]
]:
    _buffer: IBuffer[datetime] = buffer or MemoryBuffer(capacity=5)
    _lock = asyncio.Lock()

    def decorator(
        func: Callable[P, Coroutine[Any, Any, T]],
    ) -> Callable[P, Coroutine[Any, Any, T]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            nonlocal _buffer, _lock
            async with _lock:
                capacity = await _buffer.capacity()
                if capacity >= max_calls:
                    wait_time = (
                        await _buffer.get()
                        + timedelta(seconds=per_seconds)
                        - datetime.now()
                    ).total_seconds()
                    if wait_time > 0:
                        logger.warning("[rate_limit] Waiting %.2fs ...", wait_time)
                        await asyncio.sleep(wait_time)
                await _buffer.put(datetime.now(UTC))

            return await func(*args, **kwargs)

        return wrapper

    return decorator
