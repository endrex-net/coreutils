import logging
import time
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from coreutils.prometheus.metrics.scheduler import (
    job_duration_hist,
    job_failure_counter,
)


log = logging.getLogger(__name__)

P = ParamSpec("P")
RT = TypeVar("RT")

FuncType = Callable[P, Awaitable[RT]]


def monitor_async_job(job_name: str) -> Callable:
    def decorator(func: FuncType) -> FuncType:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> RT:  # type:ignore[valid-type]
            start = time.monotonic()
            try:
                result = await func(*args, **kwargs)
            except Exception:
                job_failure_counter.labels(job_name=job_name).inc()
                log.exception("Error in job %s", job_name)
                raise
            duration = time.monotonic() - start
            job_duration_hist.labels(job_name=job_name).observe(duration)
            return result

        return wrapper

    return decorator
