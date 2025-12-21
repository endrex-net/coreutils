import json
from collections.abc import Sequence
from dataclasses import asdict
from http import HTTPStatus
from typing import Any, Union

from dishka import AsyncContainer
from faststream.asgi.handlers import get
from faststream.asgi.response import AsgiResponse
from faststream.asgi.types import ASGIApp, Scope
from faststream.specification.schema import Tag, TagDict

from coreutils.healthcheck.readiness_runner import ReadinessRunner


def make_liveness_handler(
    *,
    include_in_schema: bool = True,
    description: str | None = None,
    tags: Sequence[Union["Tag", "TagDict", dict[str, Any]]] | None = None,
    unique_id: str | None = None,
) -> ASGIApp:
    @get(
        include_in_schema=include_in_schema,
        description=description,
        tags=tags,
        unique_id=unique_id,
    )
    async def get_liveness_check(scope: Scope) -> AsgiResponse:
        return AsgiResponse(
            status_code=HTTPStatus.OK,
            headers={"Content-Type": "application/json"},
            body=json.dumps({"ok": True}).encode("utf-8"),
        )

    return get_liveness_check


def make_readiness_handler(
    *,
    container: AsyncContainer,
    include_in_schema: bool = True,
    description: str | None = None,
    tags: Sequence[Union["Tag", "TagDict", dict[str, Any]]] | None = None,
    unique_id: str | None = None,
) -> ASGIApp:
    @get(
        include_in_schema=include_in_schema,
        description=description,
        tags=tags,
        unique_id=unique_id,
    )
    async def get_readiness_checks(scope: Scope) -> AsgiResponse:
        readiness_runner = await container.get(ReadinessRunner)
        result = await readiness_runner.run()
        return AsgiResponse(
            status_code=HTTPStatus.OK if result.ok else HTTPStatus.SERVICE_UNAVAILABLE,
            headers={"Content-Type": "application/json"},
            body=json.dumps(asdict(result)).encode("utf-8"),
        )

    return get_readiness_checks
