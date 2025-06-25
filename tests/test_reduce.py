import asyncio

import pytest

from coreutils import AsyncReducer, reduced


@pytest.fixture
def async_reducer() -> AsyncReducer:
    return AsyncReducer()


async def test_async_reducer_simple(async_reducer: AsyncReducer):
    async def add(a, b):
        return a + b

    result = await async_reducer(add(2, 3), ident="add")
    assert result == 5


async def test_async_reducer_multiple_calls(async_reducer: AsyncReducer):
    async def add(a, b):
        return a + b

    result1 = await async_reducer(add(2, 3), ident="add_2_3")
    result2 = await async_reducer(add(4, 5), ident="add_4_5")
    assert result1 == 5
    assert result2 == 9


async def test_async_reducer_concurrent_calls_reduced(async_reducer):
    count = 0

    async def add(a, b):
        nonlocal count
        await asyncio.sleep(0.1)
        count += 1
        return a + b

    result1 = async_reducer(add(2, 3), ident="add_2_3")
    result2 = async_reducer(add(2, 3), ident="add_2_3")
    await asyncio.gather(result1, result2)
    assert count == 1


async def test_reduced_decorator(async_reducer):
    class TestClass:
        _reducer = async_reducer

        @reduced()
        async def add(self, a, b):
            return a + b

    test_instance = TestClass()
    result = await test_instance.add(2, 3)
    assert result == 5


async def test_reduced_decorator_multiple_calls():
    class TestClass:
        def __init__(self):
            self._reducer = AsyncReducer()

        @reduced()
        async def add(self, a, b):
            return a + b

    test_instance = TestClass()
    result1 = await test_instance.add(2, 3)
    result2 = await test_instance.add(4, 5)
    assert result1 == 5
    assert result2 == 9


async def test_reduced_decorator_concurrent_calls_reduced():
    count = 0

    class TestClass:
        def __init__(self):
            self._reducer = AsyncReducer()

        @reduced()
        async def add(self, a, b):
            await asyncio.sleep(0.1)
            nonlocal count
            count += 1
            return a + b

    test_instance = TestClass()
    result1 = test_instance.add(2, 3)
    result2 = test_instance.add(2, 3)
    await asyncio.gather(result1, result2)
    assert count == 1
