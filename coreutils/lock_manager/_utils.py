from collections.abc import Hashable
from contextvars import ContextVar


_current_keys: ContextVar[set[Hashable] | None] = ContextVar(
    "current_lock_keys",
    default=None,
)


def get_current_keys() -> set[Hashable]:
    keys = _current_keys.get()
    if keys is None:
        keys = set()
        _current_keys.set(keys)
    return keys
