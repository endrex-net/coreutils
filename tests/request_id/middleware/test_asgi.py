from httpx import AsyncClient


async def test_request_id(client: AsyncClient):
    response = await client.get("/api/ping")
    assert response.headers["x-correlation-id"]


async def test_unique_request_id(client: AsyncClient):
    response1 = await client.get("/api/ping")
    response2 = await client.get("/api/ping")
    assert (
        response1.headers["x-correlation-id"] != response2.headers["x-correlation-id"]
    )
