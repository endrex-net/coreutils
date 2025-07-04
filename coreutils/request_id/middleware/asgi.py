import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from uuid import uuid4

from starlette.datastructures import MutableHeaders

from coreutils.request_id.context import correlation_id
from coreutils.request_id.sentry import get_sentry_extension
from coreutils.request_id.utils import (
    REQUEST_HEADER,
    is_valid_uuid4,
    set_request_id,
)


if TYPE_CHECKING:
    from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger("asgi_correlation_id")


@dataclass
class AsgiCorrelationIdMiddleware:
    app: "ASGIApp"

    header_name: str = REQUEST_HEADER
    generator: Callable[[], str] = field(default=lambda: uuid4().hex)
    validator: Callable[[str], bool] | None = field(default=is_valid_uuid4)
    transformer: Callable[[str], str] | None = field(default=lambda x: x)
    update_request_header: bool = True

    async def __call__(self, scope: "Scope", receive: "Receive", send: "Send") -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        # Try to load request ID from the request headers
        headers = MutableHeaders(scope=scope)
        header_value = headers.get(self.header_name.lower())

        request_id = set_request_id(
            default_value=header_value,
            generator=self.generator,
            validator=self.validator,
            transformer=self.transformer,
        )

        # Update the request headers if needed
        if request_id != header_value and self.update_request_header is True:
            headers[self.header_name] = request_id

        self.sentry_extension(request_id)

        async def handle_outgoing_request(message: "Message") -> None:
            if message["type"] == "http.response.start" and correlation_id.get():
                headers = MutableHeaders(scope=message)
                headers.append(self.header_name, correlation_id.get())  # type: ignore[arg-type]

            await send(message)

        await self.app(scope, receive, handle_outgoing_request)
        return

    def __post_init__(self) -> None:
        self.sentry_extension = get_sentry_extension()
