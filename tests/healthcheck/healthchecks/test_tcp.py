import socket
from collections.abc import AsyncIterator

import pytest
from asyncly.srvmocker import MockService, start_service

from coreutils.healthcheck.healthchecks.tcp import TcpConnectHealthCheck


async def test_tcp_connect_healthcheck_ok(mock_server: MockService) -> None:
    check = TcpConnectHealthCheck(
        name="smtp",
        host=mock_server.url.host,
        port=mock_server.url.port,
        timeout_s=0.5,
    )
    res = await check.check()
    assert res.ok is True
    assert res.latency_ms is not None


async def test_tcp_connect_healthcheck_fails_when_port_closed() -> None:
    port = _find_unused_port()
    check = TcpConnectHealthCheck(
        name="smtp", host="127.0.0.1", port=port, timeout_s=0.05
    )

    res = await check.check()
    assert res.ok is False
    assert res.error is not None


@pytest.fixture
async def mock_server() -> AsyncIterator[MockService]:
    async with start_service(routes=[]) as service:
        yield service


def _find_unused_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return int(port)
