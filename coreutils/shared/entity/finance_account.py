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
        return self.get_primary_asset(self.type)

    @cached_property
    def secondary_assets(self) -> Iterable[AssetType]:
        return self.get_secondary_assets(self.type)

    @staticmethod
    def get_primary_asset(finance_account_type: FinanceAccountType) -> AssetType:
        if finance_account_type == FinanceAccountType.BINANCE:
            return AssetType("USDC")

        if finance_account_type == FinanceAccountType.BYBIT:
            return AssetType("USDT")

        raise ValueError(f"{finance_account_type} not supported")

    @staticmethod
    def get_secondary_assets(
        finance_account_type: FinanceAccountType,
    ) -> Iterable[AssetType]:
        if finance_account_type == FinanceAccountType.BINANCE:
            return [AssetType("USDT")]

        if finance_account_type == FinanceAccountType.BYBIT:
            return []

        raise ValueError(f"{finance_account_type} not supported")
