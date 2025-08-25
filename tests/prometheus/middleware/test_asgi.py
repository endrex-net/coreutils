from http import HTTPStatus

from httpx import AsyncClient


async def test_metrics__status_code(client: AsyncClient):
    response = await client.get("/metrics/")
    assert response.status_code == HTTPStatus.OK


async def test_metrics__filter_metrics(client: AsyncClient):
    response = await client.get("/metrics/")
    assert "/metrics" not in response.text


async def test_metrics__stat(client: AsyncClient):
    await client.get("/api/ping")
    response = await client.get("/metrics/")
    assert "/api/ping" in response.text
    assert 'http_status="200"' in response.text
    assert "rest_request_count_total" in response.text
    assert "rest_request_count_created" in response.text
    assert "rest_request_latency_seconds_sum" in response.text
    assert "rest_request_latency_seconds_created" in response.text


async def test_metrics__error(client: AsyncClient):
    await client.get("/api/error")
    response = await client.get("/metrics/")
    assert "/error" in response.text
    assert 'http_status="500"' in response.text
    assert "rest_request_count_total" in response.text
    assert "rest_request_count_created" in response.text
    assert "rest_request_latency_seconds_sum" in response.text
    assert "rest_request_latency_seconds_created" in response.text
