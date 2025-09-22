from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from typing import NewType


AssetType = NewType("AssetType", str)


@dataclass(frozen=True, slots=True, kw_only=True)
class Asset:
    type: AssetType
    amount: Decimal
    amount_usd: Decimal


@dataclass(frozen=True, slots=True, kw_only=True)
class AssetPair:
    base_asset: AssetType
    quote_asset: AssetType

    @property
    def symbol(self) -> str:
        return f"{self.base_asset}{self.quote_asset}"

    def __str__(self) -> str:
        return self.symbol

    @classmethod
    def parse_trading_pair(cls, symbol: str, quote_assets: Iterable[str]) -> AssetPair:
        stripped_symbol = (
            symbol.strip().replace(" ", "").replace("-", "").replace("/", " ")
        )

        for currency in sorted(quote_assets, key=len, reverse=True):
            if stripped_symbol.endswith(currency):
                return AssetPair(
                    base_asset=AssetType(stripped_symbol[: -len(currency)]),
                    quote_asset=AssetType(currency),
                )

        raise ValueError(f"Unsupported trading pair format: {stripped_symbol}")
