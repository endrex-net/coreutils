from __future__ import annotations

from collections.abc import Iterable, MutableMapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum, unique
from functools import cached_property
from types import MappingProxyType

from coreutils.shared.entity.asset import Asset, AssetType
from coreutils.shared.entity.finance_account import FinanceAccount, FinanceAccountType
from coreutils.shared.entity.transfer import Transfer
from coreutils.shared.value_object.ids import FinanceAccountId, WalletId


@unique
class WalletType(StrEnum):
    SPOT = "SPOT"
    MARGIN = "MARGIN"
    FUTURES = "FUTURES"


FINANCE_ACCOUNT_WALLET_MAPPING: MappingProxyType[
    FinanceAccountType, Sequence[WalletType]
] = MappingProxyType(
    {
        FinanceAccountType.BINANCE: [
            WalletType.SPOT,
            WalletType.MARGIN,
            WalletType.FUTURES,
        ],
        FinanceAccountType.BYBIT: [WalletType.FUTURES],
    }
)


@dataclass(slots=True, kw_only=True)
class Wallet:
    id: WalletId
    type: WalletType

    finance_account_id: FinanceAccountId
    finance_account: FinanceAccount

    assets: MutableMapping[AssetType, Asset] = field(default_factory=dict)
    total_assets_usd: Decimal = Decimal(0)

    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None

    @property
    def primary_asset(self) -> AssetType:
        return self.finance_account.primary_asset

    @property
    def secondary_assets(self) -> Iterable[AssetType]:
        return self.finance_account.secondary_assets

    @property
    def amount_primary_asset(self) -> Decimal:
        asset = self.assets.get(self.primary_asset)
        return asset.amount if asset else Decimal(0)

    @cached_property
    def client_balance_usd(self) -> Decimal:
        return self.calculate_client_balance(self)

    @cached_property
    def trader_balance_usd(self) -> Decimal:
        return self.calculate_trader_balance(self)

    @staticmethod
    def calculate_client_balance(wallet: Wallet) -> Decimal:
        return Decimal(
            sum(
                asset.amount_usd
                for asset in wallet.assets.values()
                if asset.type not in wallet.secondary_assets
            )
        )

    @staticmethod
    def calculate_trader_balance(wallet: Wallet) -> Decimal:
        return Decimal(sum(asset.amount_usd for asset in wallet.assets.values()))

    def update_assets(self, *, assets: Sequence[Asset]) -> None:
        for asset in assets:
            self.assets[asset.type] = asset
        self._recalc_totals()

    def apply_transfer_delta(self, *, transfer: Transfer) -> None:
        current = self.assets.get(transfer.type)

        if current is None:
            if transfer.amount < 0:
                raise ValueError(
                    f"Negative balance for {transfer.type}: {transfer.amount}"
                )
            self.assets[transfer.type] = Asset(
                type=transfer.type,
                amount=transfer.amount,
                amount_usd=transfer.amount_usd,
            )
            self._recalc_totals()
            return

        new_amount = current.amount + transfer.amount
        new_amount_usd = current.amount_usd + transfer.amount_usd

        if new_amount < 0:
            raise ValueError(f"Negative balance for {transfer.type}: {new_amount}")
        if new_amount == 0:
            self.assets.pop(transfer.type)
        else:
            self.assets[transfer.type] = Asset(
                type=transfer.type,
                amount=new_amount,
                amount_usd=new_amount_usd,
            )

        self._recalc_totals()

    def _recalc_totals(self) -> None:
        total_usd = Decimal(0)

        for asset in self.assets.values():
            total_usd += asset.amount_usd

        self.total_assets_usd = total_usd
