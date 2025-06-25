from abc import abstractmethod
from typing import Protocol


class IBuffer[T](Protocol):
    @abstractmethod
    async def put(self, item: T) -> None: ...

    @abstractmethod
    async def get(self) -> T: ...

    @abstractmethod
    async def capacity(self) -> int: ...
