from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from http import HTTPMethod
from typing import Any
from uuid import UUID

from coreutils.shared.entity.finance_account import (
    FinanceAccountType,
)
from coreutils.shared.entity.wallet import WalletType
from coreutils.shared.value_object.ids import ExchangeId, FinanceAccountId, UserId


@dataclass(frozen=True, slots=True, kw_only=True)
class SignerCreateFinanceAccount:
    user_id: UserId
    type: FinanceAccountType
    wallet_types: Sequence[WalletType]
    api_key: str
    api_secret: str
    master_finance_account_id: FinanceAccountId | None
    auth_integration_id: UUID | None


@dataclass(frozen=True, slots=True, kw_only=True)
class SignerUpdateFinanceAccount:
    id: FinanceAccountId
    api_key: str
    api_secret: str


@dataclass(frozen=True, slots=True, kw_only=True)
class SignerFinanceAccount:
    id: FinanceAccountId
    user_id: UserId
    type: FinanceAccountType
    is_valid: bool
    wallet_types: Sequence[WalletType]
    exchange_id: ExchangeId
    master_finance_account_id: FinanceAccountId | None
    auth_integration_id: UUID | None


@dataclass(frozen=True, slots=True, kw_only=True)
class SignerSignRequest:
    method: HTTPMethod
    endpoint: str
    query: Mapping[str, Any] | None = None
    body: Mapping[str, Any] | None = None
    recv_window: int | None = None
    timestamp_ms: int | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class SignerSignedResponse:
    method: HTTPMethod
    url: str
    headers: Mapping[str, str]
    body_b64: str
    content_type: str | None


@dataclass(frozen=True, slots=True, kw_only=True)
class SignerSignWebsocketRequest:
    stream: str


@dataclass(frozen=True, slots=True, kw_only=True)
class SignerSignWebsocketResponse:
    url: str
    headers: Mapping[str, str] | None
    query: Mapping[str, str] | None
    expires_in_sec: int | None
