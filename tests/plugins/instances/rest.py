from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from prometheus_client import make_asgi_app
from starlette.applications import Starlette
from starlette.middleware.errors import ServerErrorMiddleware
from starlette.responses import JSONResponse

from coreutils.prometheus.middleware.asgi import AsgiPrometheusMiddleware
from coreutils.prometheus.registry import prometheus_registry
from coreutils.request_id.middleware.asgi import AsgiCorrelationIdMiddleware


@pytest.fixture
def app() -> Starlette:
    app = Starlette(debug=True)
    app.add_middleware(AsgiPrometheusMiddleware)
    app.add_middleware(AsgiCorrelationIdMiddleware)
    app.add_middleware(ServerErrorMiddleware)

    @app.route("/api/ping")
    async def ping(request):
        return JSONResponse({"message": "pong"})

    @app.route("/api/error")
    async def error(request):
        raise Exception("error")

    app.mount("/metrics", make_asgi_app(registry=prometheus_registry))
    return app


@pytest.fixture
async def client(app: Starlette) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as _client:
        yield _client
