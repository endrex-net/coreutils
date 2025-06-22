import asyncio

from aiocache import SimpleMemoryCache

from coreutils.cache import cached


class TestCached:
    def __init__(self):
        self._cache = SimpleMemoryCache()
        self.counter = 0

    @cached(ttl=60)
    async def add(self, a, b):
        await asyncio.sleep(0.1)
        self.counter += 1
        return a + b


async def test_cached_method_result():
    instance = TestCached()
    result1 = await instance.add(2, 3)
    result2 = await instance.add(2, 3)
    assert result1 == result2 == 5


async def test_cached_method_counter():
    instance = TestCached()
    await instance.add(2, 3)
    await instance.add(2, 3)
    assert instance.counter == 1


async def test_cached_method_different_args():
    instance = TestCached()
    result1 = await instance.add(2, 3)
    result2 = await instance.add(4, 5)
    assert result1 == 5
    assert result2 == 9


async def test_cached_method_different_args_counter():
    instance = TestCached()
    await instance.add(2, 3)
    await instance.add(4, 5)
    assert instance.counter == 2


async def test_cached_method_ttl():
    class TestCached:
        def __init__(self):
            self._cache = SimpleMemoryCache()
            self.counter = 0

        @cached(ttl=0.001)
        async def add(self, a, b):
            self.counter += 1
            return a + b

    instance = TestCached()
    await instance.add(2, 3)
    await asyncio.sleep(0.1)
    await instance.add(2, 3)
    assert instance.counter == 2
