import asyncio
import logging
import time
from unittest.mock import MagicMock

import pytest

from coreutils.timeit import async_timeit, timeit


@pytest.fixture
def logger():
    logger = logging.getLogger("test_logger")
    return MagicMock(logger)


def test_timeit_sync(logger):
    @timeit(logger=logger)
    def add(a, b):
        time.sleep(0.1)
        return a + b

    add(2, 3)
    logger.info.assert_called_once_with(
        {
            "event": "execution-time",
            "func_name": "add",
            "time": pytest.approx(0.1, abs=1e-1),
        }
    )


async def test_timeit_async(logger):
    @async_timeit(logger=logger)
    async def add(a, b):
        await asyncio.sleep(0.1)
        return a + b

    await add(2, 3)
    logger.info.assert_called_once_with(
        {
            "event": "execution-time",
            "func_name": "add",
            "time": pytest.approx(0.1, abs=1e-1),
        }
    )


def test_timeit_custom_time_func(logger):
    def custom_time_func():
        return 42

    @timeit(logger=logger, time_func=custom_time_func)
    def add(a, b):
        return a + b

    add(2, 3)
    logger.info.assert_called_once_with({"event": "execution-time", "func_name": "add", "time": 0})


def test_timeit_invalid_time_func(logger):
    def custom_time_func():
        raise ValueError("Invalid time func")

    @timeit(logger=logger, time_func=custom_time_func)
    def add(a, b):
        return a + b

    with pytest.raises(ValueError):
        add(2 + 3)


def test_timeit_invalid_logger(logger):
    @timeit(logger="invalid_logger")
    def add(a, b):
        return a + b

    with pytest.raises(TypeError):
        add()


def test_timeit_no_logger():
    @timeit()
    def add(a, b):
        return a + b

    result = add(2, 3)
    assert result == 5
