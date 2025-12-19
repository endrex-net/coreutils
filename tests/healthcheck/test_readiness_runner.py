import asyncio
from dataclasses import dataclass

from coreutils.healthcheck.dto import CheckResult
from coreutils.healthcheck.readiness_runner import ReadinessRunner


@dataclass(slots=True)
class DummyCheck:
    name: str
    delay_s: float = 0.0
    result: CheckResult | None = None
    exc: Exception | None = None

    async def check(self) -> CheckResult:
        if self.delay_s:
            await asyncio.sleep(self.delay_s)
        if self.exc is not None:
            raise self.exc
        assert self.result is not None
        return self.result


async def test_runner_collects_results() -> None:
    c1 = DummyCheck(name="postgres", result=CheckResult(ok=True, latency_ms=1))
    c2 = DummyCheck(name="redis", result=CheckResult(ok=False, error="down"))
    runner = ReadinessRunner(checks=[c1, c2], timeout_s=1.0)

    res = await runner.run()

    assert set(res.checks.keys()) == {"postgres", "redis"}
    assert res.checks["postgres"].ok is True
    assert res.checks["redis"].ok is False
    assert res.checks["redis"].error == "down"


async def test_runner_marks_timeout_bucket_when_some_pending() -> None:
    fast = DummyCheck(name="fast", delay_s=0.0, result=CheckResult(ok=True))
    slow = DummyCheck(name="slow", delay_s=0.2, result=CheckResult(ok=True))
    runner = ReadinessRunner(checks=[fast, slow], timeout_s=0.01)

    res = await runner.run()

    # fast успел, slow нет => будет общий маркер таймаута
    assert "fast" in res.checks
    assert res.checks["fast"].ok is True
    assert "_timeout" in res.checks
    assert res.checks["_timeout"].ok is False
    assert res.checks["_timeout"].error == "Readiness timeout"


async def test_runner_converts_unhandled_exception_to_failed_checkresult() -> None:
    bad = DummyCheck(name="nats", exc=RuntimeError("boom"))
    runner = ReadinessRunner(checks=[bad], timeout_s=1.0)

    res = await runner.run()

    assert "nats" in res.checks
    assert res.checks["nats"].ok is False
    assert res.checks["nats"].error is not None
    assert "RuntimeError" in res.checks["nats"].error
    assert "boom" in res.checks["nats"].error
