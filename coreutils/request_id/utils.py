import logging
from collections.abc import Callable
from typing import Final
from uuid import UUID, uuid4

from coreutils.request_id.context import correlation_id


logger = logging.getLogger(__name__)


REQUEST_HEADER: Final[str] = "X-Correlation-Id"

FAILED_VALIDATION_MESSAGE: Final[str] = "Generated new request ID (%s), since request header value failed validation"


def is_valid_uuid4(uuid_: str) -> bool:
    try:
        return UUID(uuid_).version == 4
    except ValueError:
        return False


def set_request_id(
    default_value: str | None = None,
    generator: Callable[[], str] = lambda: uuid4().hex,
    validator: Callable[[str], bool] | None = is_valid_uuid4,
    transformer: Callable[[str], str] | None = None,
) -> str:
    validation_failed = False
    if not default_value:
        # Generate request ID if none was found
        id_value = generator()
    elif validator and not validator(default_value):
        # Also generate a request ID if one was found, but it was deemed invalid
        validation_failed = True
        id_value = generator()
    else:
        # Otherwise, use the found request ID
        id_value = default_value

    # Clean/change the ID if needed
    if transformer:
        id_value = transformer(id_value)

    if validation_failed is True:
        logger.warning(FAILED_VALIDATION_MESSAGE, id_value)

    correlation_id.set(id_value)

    return id_value
