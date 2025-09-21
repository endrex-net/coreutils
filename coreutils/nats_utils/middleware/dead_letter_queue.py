from __future__ import annotations

import logging
import traceback
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Self
from uuid import uuid4

from faststream import BaseMiddleware
from faststream.nats import NatsBroker


if TYPE_CHECKING:
    from faststream.broker.message import StreamMessage
    from faststream.types import AsyncFuncAny

log = logging.getLogger("faststream")


@dataclass(frozen=True)
class DeadLetterMessage:
    id: str
    original_subject: str
    original_message: bytes
    error_message: str
    error_type: str
    error_traceback: str
    failed_at: datetime
    retry_count: int = 0
    correlation_id: str | None = None


class DeadLetterQueueMiddleware(BaseMiddleware):
    def __init__(
        self,
        broker: NatsBroker,
        dead_letter_stream: str,
        dead_letter_subject: str,
        message: Any | None = None,
    ) -> None:
        self.__broker = broker
        self.__dlq_stream = dead_letter_stream
        self.__dlq_subject = dead_letter_subject

        super().__init__(message)

    def __call__(self, _message: Any) -> Self:
        return self

    async def after_consume_with_message(self, message: StreamMessage[Any], err: Exception | None) -> None:
        if err is not None:
            try:
                await self._send_to_dlq(message, err)
            except Exception:
                log.exception("Failed to send message to DLQ")

        await self.after_consume(err)

    async def _send_to_dlq(self, message: StreamMessage[Any], error: Exception) -> None:
        metadata = getattr(message.raw_message, "metadata", None)
        retry_count = getattr(metadata, "num_delivered", 1) - 1 if metadata else 0
        correlation_id = getattr(message, "correlation_id", None)

        dlq_message = DeadLetterMessage(
            id=str(uuid4()),
            original_subject=message.raw_message.subject,
            original_message=message.body,
            error_message=str(error),
            error_type=type(error).__name__,
            error_traceback=traceback.format_exc(),
            failed_at=datetime.now(UTC),
            retry_count=retry_count,
            correlation_id=correlation_id,
        )

        await self.__broker.publish(dlq_message, subject=self.__dlq_subject, stream=self.__dlq_stream)

        log.error(
            "Message sent to DLQ. Subject: %s, Error: %s, Retry count: %d",
            message.raw_message.subject,
            error,
            retry_count,
        )

    async def consume_scope(
        self,
        call_next: AsyncFuncAny,
        message: StreamMessage[Any],
    ) -> Any:
        err: Exception | None = None
        try:
            result = await call_next(await self.on_consume(message))

        except Exception as e:  # noqa: BLE001
            err = e

        else:
            return result

        finally:
            await self.after_consume_with_message(message, err)
