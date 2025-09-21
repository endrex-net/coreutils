from types import MappingProxyType
from typing import NoReturn

from aiohttp import ClientResponse
from asyncly import BaseHttpClient, ResponseHandlersType
from asyncly.client.handlers.pydantic import parse_model

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


class SignerClient(BaseHttpClient):
    FINANCE_ACCOUNT_HANDLERS: ResponseHandlersType = MappingProxyType(
        {
            "2xx": parse_model(SignerFinanceAccount),
            "*": raise_signer_exception,
        }
    )

    SIGNED_RESPONSE_HANDLERS: ResponseHandlersType = MappingProxyType(
        {
            "2xx": parse_model(SignerSignedResponse),
            "*": raise_signer_exception,
        }
    )

    WEBSOCKET_RESPONSE_HANDLERS: ResponseHandlersType = MappingProxyType(
        {
            "2xx": parse_model(SignerSignWebsocketResponse),
            "*": raise_signer_exception,
        }
    )

    async def create_finance_account(
        self,
        finance_account: SignerCreateFinanceAccount,
    ) -> SignerFinanceAccount:
        return await self._make_req(
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
            handlers=self.FINANCE_ACCOUNT_HANDLERS,
        )

    async def update_finance_account(
        self,
        finance_account: SignerUpdateFinanceAccount,
    ) -> SignerFinanceAccount:
        return await self._make_req(
            method="PATCH",
            url=self._url / f"api/v1/finance-account/{finance_account.id}",
            json={
                "properties": {
                    "api_key": finance_account.properties.api_key,
                    "api_secret": finance_account.properties.api_secret,
                },
            },
            handlers=self.FINANCE_ACCOUNT_HANDLERS,
        )

    async def get_finance_account(
        self,
        finance_account_id: str,
    ) -> SignerFinanceAccount:
        return await self._make_req(
            method="GET",
            url=self._url / f"api/v1/finance-account/{finance_account_id}",
            handlers=self.FINANCE_ACCOUNT_HANDLERS,
        )

    async def sign_request(
        self,
        finance_account_id: str,
        sign_request: SignerSignRequest,
    ) -> SignerSignedResponse:
        return await self._make_req(
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
            handlers=self.SIGNED_RESPONSE_HANDLERS,
        )

    async def sign_websocket(
        self,
        finance_account_id: str,
        websocket_request: SignerSignWebsocketRequest,
    ) -> SignerSignWebsocketResponse:
        return await self._make_req(
            method="POST",
            url=self._url / f"api/v1/finance-account/{finance_account_id}/sign-ws",
            json={
                "stream": websocket_request.stream,
            },
            handlers=self.WEBSOCKET_RESPONSE_HANDLERS,
        )
