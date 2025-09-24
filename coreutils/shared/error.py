from __future__ import annotations

import abc
from collections.abc import Mapping
from types import TracebackType
from typing import Any


class Error(Exception, abc.ABC):
    message: str | None
    code: str | None

    def __init__(
        self,
        message: str,
        code: str | None = None,
        traceback: TracebackType | None = None,
        data: Mapping[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.data = data or {}

        if traceback is not None:
            self.with_traceback(traceback)
