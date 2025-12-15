import pytest
from faststream import StreamMessage
from faststream._internal.context import ContextRepo
from starlette.applications import Starlette

from coreutils.request_id import (
    correlation_id,
    set_request_id,
)
from coreutils.request_id.middleware.asgi import AsgiCorrelationIdMiddleware
from coreutils.request_id.middleware.broker import BrokerCorrelationIdMiddleware


@pytest.fixture
def app() -> Starlette:
    return Starlette()


@pytest.fixture
def asgi_middleware(app) -> AsgiCorrelationIdMiddleware:
    return AsgiCorrelationIdMiddleware(app)


@pytest.fixture
def broker_middleware():
    return BrokerCorrelationIdMiddleware(None, context=ContextRepo())


async def test_asgi_middleware_set_request_id(
    asgi_middleware: AsgiCorrelationIdMiddleware,
):
    scope = {"type": "http", "headers": [], "path": "/"}

    async def send(message) -> None: ...

    await asgi_middleware(scope, lambda: None, send)

    assert correlation_id.get() is not None


async def test_asgi_middleware_update_request_header(
    asgi_middleware: AsgiCorrelationIdMiddleware,
):
    scope = {"type": "http", "headers": [("x-correlation-id", "old-id")], "path": "/"}

    async def send(message) -> None: ...

    await asgi_middleware(scope, lambda: None, send)

    assert correlation_id.get() != "old-id"


async def test_broker_middleware_set_request_id(
    broker_middleware: BrokerCorrelationIdMiddleware,
):
    message = {"headers": {}}

    await broker_middleware.on_consume(StreamMessage(raw_message=message, body=b""))

    assert correlation_id.get() is not None


async def test_broker_middleware_update_request_header(
    broker_middleware: BrokerCorrelationIdMiddleware,
):
    message = {"headers": {"x-correlation-id": "old-id"}}

    await broker_middleware.on_consume(StreamMessage(raw_message=message, body=b""))

    assert correlation_id.get() != "old-id"


def test_set_request_id():
    request_id = set_request_id()

    assert request_id is not None


def test_set_request_id_with_default_value():
    default_value = "custom-id"
    request_id = set_request_id(default_value=default_value, validator=lambda x: True)

    assert request_id == default_value


def test_set_request_id_with_invalid_default_value():
    default_value = "invalid-id"
    request_id = set_request_id(default_value=default_value)

    assert request_id != default_value


def test_set_request_id_with_validator():
    def validator(request_id):
        return request_id.startswith("custom-")

    request_id = set_request_id(default_value="custom-id", validator=validator)

    assert request_id.startswith("custom-")
