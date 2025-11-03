from http import HTTPStatus
from typing import Any, NoReturn

from aiohttp import ClientResponse, ClientSession
from yarl import URL

from coreutils.signer.dto import (
    SignerCreateFinanceAccount,
    SignerFinanceAccount,
    SignerSignedResponse,
    SignerSignRequest,
    SignerSignWebsocketRequest,
    SignerSignWebsocketResponse,
    SignerUpdateFinanceAccount,
)
from coreutils.signer.exceptions import SignerClientException


async def raise_signer_exception(response: ClientResponse) -> NoReturn:
    data = await response.json()
    raise SignerClientException(
        code=data["code"],
        message=data["message"],
        data=data,
    )


class SignerClient:
    def __init__(
        self, url: URL | str, session: ClientSession, client_name: str = "SignerClient"
    ):
        self._url = url if isinstance(url, URL) else URL(url)
        self._session = session
        self._client_name = client_name

    @property
    def url(self) -> URL:
        return self._url

    async def _make_request(
        self,
        method: str,
        url: URL,
        json: dict | None = None,
    ) -> dict[str, Any] | None:
        """Выполняет HTTP запрос и обрабатывает ответ"""
        async with self._session.request(
            method=method,
            url=url,
            json=json,
        ) as response:
            # Обработка успешных ответов (2xx)
            if 200 <= response.status < 300:
                if response.status == HTTPStatus.NO_CONTENT:
                    return None
                return await response.json()
            # Обработка ошибок
            else:
                await raise_signer_exception(response)

    async def create_finance_account(
        self,
        finance_account: SignerCreateFinanceAccount,
    ) -> SignerFinanceAccount:
        response = await self._make_request(
            method="POST",
            url=self._url / "api/v1/finance-account",
            json={
                "user_id": str(finance_account.user_id),
                "type": finance_account.type,
                "wallet_types": finance_account.wallet_types,
                "properties": {
                    "api_key": finance_account.properties.api_key,
                    "api_secret": finance_account.properties.api_secret,
                },
            },
        )
        return SignerFinanceAccount(**response)  # type: ignore[arg-type]

    async def update_finance_account(
        self,
        finance_account: SignerUpdateFinanceAccount,
    ) -> SignerFinanceAccount:
        response = await self._make_request(
            method="PATCH",
            url=self._url / f"api/v1/finance-account/{finance_account.id}",
            json={
                "properties": {
                    "api_key": finance_account.properties.api_key,
                    "api_secret": finance_account.properties.api_secret,
                },
            },
        )
        return SignerFinanceAccount(**response)  # type: ignore[arg-type]

    async def delete_finance_account(
        self,
        finance_account_id: str,
    ) -> None:
        await self._make_request(
            method="DELETE",
            url=self._url / f"api/v1/finance-account/{finance_account_id}",
        )

    async def invalidate_finance_account(
        self,
        finance_account_id: str,
    ) -> None:
        await self._make_request(
            method="POST",
            url=self._url / f"api/v1/finance-account/{finance_account_id}/invalidate",
        )

    async def get_finance_account(
        self,
        finance_account_id: str,
    ) -> SignerFinanceAccount:
        response = await self._make_request(
            method="GET",
            url=self._url / f"api/v1/finance-account/{finance_account_id}",
        )
        return SignerFinanceAccount(**response)  # type: ignore[arg-type]

    async def sign_request(
        self,
        finance_account_id: str,
        sign_request: SignerSignRequest,
    ) -> SignerSignedResponse:
        response = await self._make_request(
            method="POST",
            url=self._url / f"api/v1/finance-account/{finance_account_id}/sign",
            json={
                "method": sign_request.method,
                "endpoint": sign_request.endpoint,
                "query": sign_request.query,
                "body": sign_request.body,
                "recv_window": sign_request.recv_window,
                "timestamp_ms": sign_request.timestamp_ms,
            },
        )
        return SignerSignedResponse(**response)  # type: ignore[arg-type]

    async def sign_websocket(
        self,
        finance_account_id: str,
        websocket_request: SignerSignWebsocketRequest,
    ) -> SignerSignWebsocketResponse:
        response = await self._make_request(
            method="POST",
            url=self._url / f"api/v1/finance-account/{finance_account_id}/sign-ws",
            json={
                "stream": websocket_request.stream,
            },
        )
        return SignerSignWebsocketResponse(**response)  # type: ignore[arg-type]
