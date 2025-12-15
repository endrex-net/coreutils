import logging
from collections.abc import Awaitable, Callable
from typing import Any
from uuid import uuid4

from faststream import BaseMiddleware, StreamMessage
from faststream._internal.context.repository import ContextRepo

from coreutils.request_id.sentry import get_sentry_extension
from coreutils.request_id.utils import (
    REQUEST_HEADER,
    is_valid_uuid4,
    set_request_id,
)


logger = logging.getLogger(__name__)


class BrokerCorrelationIdMiddleware(BaseMiddleware):
    def __init__(self, msg: Any | None, /, *, context: ContextRepo) -> None:
        self.sentry_extension = get_sentry_extension()
        self.header_name = REQUEST_HEADER
        self.generator = lambda: uuid4().hex
        self.validator = is_valid_uuid4
        self.transformer = lambda x: x
        super().__init__(msg, context=context)

    async def consume_scope(
        self, call_next: Callable[[Any], Awaitable[Any]], msg: StreamMessage[Any]
    ) -> Any:
        header_value = msg.headers.get(self.header_name)

        request_id = set_request_id(
            default_value=header_value,
            generator=self.generator,
            validator=self.validator,
            transformer=self.transformer,
        )

        if request_id != header_value:
            msg.headers[self.header_name] = request_id

        return await super().consume_scope(call_next, msg)

    async def on_consume(self, msg: StreamMessage[Any]) -> StreamMessage[Any]:
        header_value = msg.headers.get(self.header_name)

        request_id = set_request_id(
            default_value=header_value,
            generator=self.generator,
            validator=self.validator,
            transformer=self.transformer,
        )

        if request_id != header_value:
            msg.headers[self.header_name] = request_id

        return msg
