import asyncio
import time
from collections.abc import Coroutine
from typing import Any


def now_ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


async def run_with_timeout[T](coro: Coroutine[Any, Any, T], *, timeout_s: float) -> T:
    return await asyncio.wait_for(coro, timeout=timeout_s)
