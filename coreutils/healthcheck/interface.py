from typing import Protocol

from coreutils.healthcheck.dto import CheckResult


class HealthCheck(Protocol):
    name: str

    async def check(self) -> CheckResult: ...
