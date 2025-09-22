from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum, unique
from functools import cached_property

from coreutils.shared.entity.asset import AssetType
from coreutils.shared.entity.wallet import WalletType
from coreutils.shared.value_object.ids import FinanceAccountId, UserId


@unique
class FinanceAccountType(StrEnum):
    BINANCE = "BINANCE"
    BYBIT = "BYBIT"


@dataclass(frozen=True, kw_only=True, slots=True)
class FinanceAccountProperties:
    connection_name: str
    api_key: str
    api_secret: str


@dataclass(frozen=True, kw_only=True, slots=True)
class FinanceAccount:
    id: FinanceAccountId
    user_id: UserId
    type: FinanceAccountType
    properties: FinanceAccountProperties
    is_valid: bool
    wallet_types: set[WalletType]

    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None

    @cached_property
    def connection_name(self) -> str:
        return self.properties.connection_name

    @cached_property
    def primary_asset(self) -> AssetType:
        if self.type == FinanceAccountType.BINANCE:
            return AssetType("USDC")

        if self.type == FinanceAccountType.BYBIT:
            return AssetType("USDT")

        raise ValueError(f"{self.type} not supported")

    @cached_property
    def secondary_assets(self) -> Iterable[AssetType]:
        if self.type == FinanceAccountType.BINANCE:
            return [AssetType("USDT")]

        if self.type == FinanceAccountType.BYBIT:
            return []

        raise ValueError(f"{self.type} not supported")
