from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from coreutils.shared.entity.asset import AssetType
from coreutils.shared.value_object.ids import WalletId


@dataclass(frozen=True, slots=True, kw_only=True)
class RawTransfer:
    type: AssetType
    amount: Decimal
    created_at: datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class Transfer:
    wallet_id: WalletId
    type: AssetType
    amount: Decimal
    amount_usd: Decimal
    created_at: datetime
