from __future__ import annotations

from collections.abc import Iterable, MutableMapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from types import MappingProxyType

from coreutils.shared.entity.asset import Asset, AssetType
from coreutils.shared.entity.finance_account import FinanceAccount
from coreutils.shared.enums.finance_account_type import FinanceAccountType
from coreutils.shared.enums.wallet_type import WalletType
from coreutils.shared.value_object.ids import FinanceAccountId, WalletId


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

    total_wallet_balance: Decimal = Decimal(0)
    total_equity: Decimal = Decimal(0)
    total_available_balance: Decimal = Decimal(0)

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
    def primary_asset_equity(self) -> Decimal:
        asset = self.assets.get(self.primary_asset)
        return asset.equity if asset else Decimal(0)
