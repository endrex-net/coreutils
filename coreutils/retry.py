import asyncio
import logging
from collections.abc import Callable, Coroutine
from datetime import datetime
from functools import wraps
from typing import (
    Any,
    ParamSpec,
    TypeVar,
)

from coreutils.counters import Statistic


Number = int | float
T = TypeVar("T")
P = ParamSpec("P")

logger = logging.getLogger(__name__)


class BackoffStatistic(Statistic):
    done: int
    attempts: int
    cancels: int
    errors: int
    sum_time: float


class RetryStatistic(BackoffStatistic):
    pass


def timeout(
    value: Number,
) -> Callable[
    [Callable[P, Coroutine[Any, Any, T]]],
    Callable[P, Coroutine[Any, Any, T]],
]:
    def decorator(
        func: Callable[P, Coroutine[Any, Any, T]],
    ) -> Callable[P, Coroutine[Any, Any, T]]:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("Function is not a coroutine function")

        @wraps(func)
        async def wrap(*args: P.args, **kwargs: P.kwargs) -> T:
            return await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=value,
            )

        return wrap

    return decorator


def asyncbackoff(  # noqa: C901
    attempt_timeout: Number | None,
    deadline: Number | None,
    pause: Number = 0,
    *exc: type[Exception],
    exceptions: tuple[type[Exception], ...] = (),
    max_tries: int | None = None,
    giveup: Callable[[Exception], bool] | None = None,
    on_attempt: Callable[[datetime], None] | None = None,
    on_exception: Callable[[Exception], None] | None = None,
    statistic_name: str | None = None,
    statistic_class: type[BackoffStatistic] = BackoffStatistic,
    repeat_on_success: bool = False,
) -> Callable[
    [Callable[P, Coroutine[Any, Any, T]]],
    Callable[P, Coroutine[Any, Any, T]],
]:
    """
    Patametric decorator that ensures that ``attempt_timeout`` and
    ``deadline`` time limits are met by decorated function.

    In case of exception function will be called again with similar
    arguments after ``pause`` seconds.

    :param statistic_name: name filed for statistic instances
    :param attempt_timeout: is maximum execution time for one
                            execution attempt.
    :param deadline: is maximum execution time for all execution attempts.
    :param pause: is time gap between execution attempts.
    :param exc: retrying when this exceptions was raised.
    :param exceptions: similar as exc but keyword only.
    :param max_tries: is maximum count of execution attempts (>= 1).
    :param giveup: is a predicate function which can decide by a given
    :param statistic_class: statistic class
    :param rate_limiter: rate limiter instance
                         for limit calls the function by period
    """

    exceptions = exc + tuple(exceptions)
    statistic = statistic_class(statistic_name)

    if not pause:
        pause = 0
    elif pause < 0:
        raise ValueError("'pause' must be positive")

    if attempt_timeout is not None and attempt_timeout < 0:
        raise ValueError("'attempt_timeout' must be positive or None")

    if deadline is not None and deadline < 0:
        raise ValueError("'deadline' must be positive or None")

    if max_tries is not None and max_tries < 1:
        raise ValueError("'max_retries' must be >= 1 or None")

    if giveup is not None and not callable(giveup):
        raise ValueError("'giveup' must be a callable or None")

    exceptions = tuple(exceptions) or ()
    exceptions += (asyncio.TimeoutError,)

    def decorator(  # noqa: C901
        func: Callable[P, Coroutine[Any, Any, T]],
    ) -> Callable[P, Coroutine[Any, Any, T]]:
        if attempt_timeout is not None:
            func = timeout(attempt_timeout)(func)

        @wraps(func)
        async def wrap(*args: P.args, **kwargs: P.kwargs) -> T:  # noqa: C901
            last_exc = None
            tries = 0

            async def run() -> Any:  # noqa: C901
                nonlocal last_exc, tries

                loop = asyncio.get_running_loop()

                while True:
                    statistic.attempts += 1
                    tries += 1
                    delta = -loop.time()

                    try:
                        if on_attempt:
                            on_attempt(datetime.now())
                        result = await asyncio.wait_for(
                            func(*args, **kwargs),
                            timeout=attempt_timeout,
                        )
                        if repeat_on_success and max_tries is not None and tries < max_tries:
                            continue
                        return result
                    except asyncio.CancelledError:
                        statistic.cancels += 1
                        raise
                    except exceptions as e:
                        statistic.errors += 1
                        last_exc = e
                        if on_exception:
                            on_exception(e)
                        if max_tries is not None and tries >= max_tries:
                            raise
                        if giveup and giveup(e):
                            raise
                        await asyncio.sleep(pause)
                    except Exception as e:
                        if on_exception:
                            on_exception(e)
                        last_exc = e
                        raise
                    finally:
                        delta += loop.time()
                        statistic.sum_time += delta
                        statistic.done += 1

            try:
                return await asyncio.wait_for(run(), timeout=deadline)
            except Exception:
                if last_exc:
                    raise last_exc
                raise

        return wrap

    return decorator


def asyncretry(
    max_tries: int | None,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    pause: Number = 0,
    giveup: Callable[[Exception], bool] | None = None,
    on_attempt: Callable[[datetime], None] | None = None,
    on_exception: Callable[[Exception], None] | None = None,
    statistic_name: str | None = None,
    repeat_on_success: bool = False,
) -> Callable[
    [Callable[P, Coroutine[Any, Any, T]]],
    Callable[P, Coroutine[Any, Any, T]],
]:
    """
    Shortcut of ``asyncbackoff(None, None, 0, Exception)``.

    In case of exception function will be called again with similar
    arguments after ``pause`` seconds.

    :param max_tries: is maximum count of execution attempts
                      (>= 1 or ``None`` means infinity).
    :param exceptions: similar as exc but keyword only.
    :param giveup: is a predicate function which can decide by a given
    :param pause: is time gap between execution attempts.
    :param statistic_name: name filed for statistic instances
    :param rate_limiter: rate limiter instance for limit calls the
                         function by period
    """

    return asyncbackoff(
        attempt_timeout=None,
        deadline=None,
        exceptions=exceptions,
        giveup=giveup,
        on_attempt=on_attempt,
        on_exception=on_exception,
        max_tries=max_tries,
        pause=pause,
        statistic_class=RetryStatistic,
        statistic_name=statistic_name,
        repeat_on_success=repeat_on_success,
    )
