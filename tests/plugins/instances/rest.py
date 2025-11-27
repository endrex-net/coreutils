from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from prometheus_client import make_asgi_app
from starlette.applications import Starlette
from starlette.middleware.errors import ServerErrorMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Route

from coreutils.prometheus.middleware.asgi import AsgiPrometheusMiddleware
from coreutils.prometheus.registry import prometheus_registry
from coreutils.request_id.middleware.asgi import AsgiCorrelationIdMiddleware


@pytest.fixture
def app() -> Starlette:
    async def ping(request):
        """/api/ping"""
        return JSONResponse({"message": "pong"})

    async def error(request):
        """/api/error"""
        raise Exception("error")

    app = Starlette(
        debug=True,
        routes=[
            Route("/api/ping", ping),
            Route("/api/error", error),
        ],
    )
    app.add_middleware(AsgiPrometheusMiddleware)
    app.add_middleware(AsgiCorrelationIdMiddleware)
    app.add_middleware(ServerErrorMiddleware)

    app.mount("/metrics", make_asgi_app(registry=prometheus_registry))
    return app


@pytest.fixture
async def client(app: Starlette) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as _client:
        yield _client
