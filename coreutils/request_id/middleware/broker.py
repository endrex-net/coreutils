import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Self
from uuid import uuid4

from faststream import BaseMiddleware
from faststream.broker.message import StreamMessage

from coreutils.request_id.sentry import get_sentry_extension
from coreutils.request_id.utils import (
    REQUEST_HEADER,
    is_valid_uuid4,
    set_request_id,
)


logger = logging.getLogger(__name__)


@dataclass
class BrokerCorrelationIdMiddleware(BaseMiddleware):
    header_name: str = REQUEST_HEADER
    generator: Callable[[], str] = field(default=lambda: uuid4().hex)
    validator: Callable[[str], bool] | None = field(default=is_valid_uuid4)
    transformer: Callable[[str], str] | None = field(default=lambda x: x)

    def __call__(self, _msg: Any) -> Self:
        return self

    async def on_consume(self, message: StreamMessage[Any]) -> StreamMessage[Any]:
        header_value = message.headers.get(self.header_name)

        request_id = set_request_id(
            default_value=header_value,
            generator=self.generator,
            validator=self.validator,
            transformer=self.transformer,
        )

        if request_id != header_value:
            message.headers[self.header_name] = request_id

        return message

    def __post_init__(self) -> None:
        self.sentry_extension = get_sentry_extension()
