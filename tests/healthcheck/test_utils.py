import asyncio

import pytest

from coreutils.healthcheck.utils import run_with_timeout


async def test_run_with_timeout_returns_value() -> None:
    async def f() -> int:
        return 123

    res = await run_with_timeout(f(), timeout_s=0.5)
    assert res == 123


async def test_run_with_timeout_propagates_timeout() -> None:
    async def slow() -> None:
        await asyncio.sleep(0.2)

    with pytest.raises(asyncio.TimeoutError):
        await run_with_timeout(slow(), timeout_s=0.01)


async def test_run_with_timeout_propagates_original_exception() -> None:
    class BoomError(RuntimeError):
        pass

    async def boom() -> None:
        raise BoomError("boom")

    with pytest.raises(BoomError):
        await run_with_timeout(boom(), timeout_s=0.5)
