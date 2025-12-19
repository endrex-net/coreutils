from unittest.mock import AsyncMock, Mock

from coreutils.healthcheck.healthchecks.postgres import PostgresHealthCheck


async def test_postgres_healthcheck_ok() -> None:
    # engine.connect() -> async context manager -> conn.execute(...)
    conn = AsyncMock()
    cm = AsyncMock()
    cm.__aenter__.return_value = conn
    cm.__aexit__.return_value = False

    engine = Mock()
    engine.connect.return_value = cm

    check = PostgresHealthCheck(engine=engine, timeout_s=0.5)
    res = await check.check()

    assert res.ok is True
    assert res.latency_ms is not None
    conn.execute.assert_awaited_once()


async def test_postgres_healthcheck_fails_on_execute_error() -> None:
    conn = AsyncMock()
    conn.execute.side_effect = RuntimeError("db down")

    cm = AsyncMock()
    cm.__aenter__.return_value = conn
    cm.__aexit__.return_value = False

    engine = Mock()
    engine.connect.return_value = cm

    check = PostgresHealthCheck(engine=engine, timeout_s=0.5)
    res = await check.check()

    assert res.ok is False
    assert res.error is not None
    assert "RuntimeError" in res.error
    assert "db down" in res.error
