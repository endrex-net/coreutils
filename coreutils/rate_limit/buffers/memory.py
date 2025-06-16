from collections import deque

from coreutils.rate_limit.buffers.base import IBuffer


class MemoryBuffer[T](IBuffer):
    _buf: deque[T]

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be > 0")

        self._buf = deque(maxlen=capacity)

    async def put(self, item: T) -> None:
        self._buf.append(item)

    async def get(self) -> T:
        return self._buf.popleft()

    async def capacity(self) -> int:
        return len(self._buf)
