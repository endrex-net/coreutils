from collections.abc import Awaitable, Callable
from functools import wraps
from logging import Logger, getLogger
from time import monotonic
from typing import ParamSpec, TypeVar


log = getLogger(__name__)


P = ParamSpec("P")
RT = TypeVar("RT")


def async_timeit(
    logger: Logger = log,
    time_func: Callable[[], float | int] = monotonic,
) -> Callable[[Callable[P, Awaitable[RT]]], Callable[P, Awaitable[RT]]]:
    def _async_timeit(
        func: Callable[P, Awaitable[RT]],
    ) -> Callable[P, Awaitable[RT]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> RT:
            start = time_func()
            result = await func(*args, **kwargs)
            logger.info(
                {
                    "event": "execution-time",
                    "func_name": func.__name__,
                    "time": time_func() - start,
                },
            )

            return result

        return wrapper

    return _async_timeit


def timeit(
    logger: Logger = log,
    time_func: Callable[[], float | int] = monotonic,
) -> Callable[[Callable[P, RT]], Callable[P, RT]]:
    def _timeit(func: Callable[P, RT]) -> Callable[P, RT]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> RT:
            start = time_func()
            result = func(*args, **kwargs)
            logger.info(
                {
                    "event": "execution-time",
                    "func_name": func.__name__,
                    "time": time_func() - start,
                },
            )

            return result

        return wrapper

    return _timeit
