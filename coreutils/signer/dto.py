from collections.abc import Mapping, Sequence
from http import HTTPMethod
from typing import Any

from coreutils.shared.base import DTO
from coreutils.shared.entity.finance_account import (
    FinanceAccountProperties,
    FinanceAccountType,
)
from coreutils.shared.entity.wallet import WalletType
from coreutils.shared.value_object.ids import FinanceAccountId, UserId


class SignerCreateFinanceAccount(DTO):
    user_id: UserId
    type: FinanceAccountType
    wallet_types: Sequence[WalletType]
    properties: FinanceAccountProperties


class SignerUpdateFinanceAccount(DTO):
    id: FinanceAccountId
    properties: FinanceAccountProperties


class SignerFinanceAccount(DTO):
    id: FinanceAccountId
    user_id: UserId
    type: FinanceAccountType
    is_valid: bool
    wallet_types: Sequence[WalletType]


class SignerSignRequest(DTO):
    method: HTTPMethod
    endpoint: str
    query: Mapping[str, Any]
    body: Mapping[str, Any]
    recv_window: int | None = None
    timestamp_ms: int | None = None


class SignerSignedResponse(DTO):
    method: HTTPMethod
    url: str
    headers: Mapping[str, str]
    body_b64: str
    content_type: str | None


class SignerSignWebsocketRequest(DTO):
    stream: str


class SignerSignWebsocketResponse(DTO):
    url: str
    headers: Mapping[str, str] | None
    query: Mapping[str, str] | None
    expires_in_sec: int | None
