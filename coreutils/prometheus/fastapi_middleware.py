import re
import time
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request, Response

from coreutils.prometheus.metrics.rest import REQUEST_COUNT, REQUEST_LATENCY


UUID_REGEX = re.compile(
    r"/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}"
)


def normalize_endpoint(path: str) -> str:
    return UUID_REGEX.sub("/{id}", path)


def is_monitorable_endpoint(path: str, route: Any | None, method: str) -> bool:
    ignore_paths = ["/monitoring", "/docs", "/metrics"]
    ignore_methods = {"OPTIONS"}

    if method in ignore_methods:
        return False

    if any(ignored in path for ignored in ignore_paths):
        return False

    if route is None:
        return False

    if not path.startswith("/api/"):
        return False

    return True


async def prometheus_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    route = request.scope.get("route")
    if not is_monitorable_endpoint(request.url.path, route, request.method):
        return await call_next(request)

    start_time = time.monotonic()
    response = await call_next(request)
    process_time = time.monotonic() - start_time

    endpoint = route.path if route else normalize_endpoint(request.url.path)

    REQUEST_LATENCY.labels(method=request.method, endpoint=endpoint).observe(
        process_time
    )
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=endpoint,
        http_status=response.status_code,
    ).inc()

    return response
