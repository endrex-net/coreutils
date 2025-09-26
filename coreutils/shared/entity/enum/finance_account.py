from enum import StrEnum, unique


@unique
class WalletType(StrEnum):
    SPOT = "SPOT"
    MARGIN = "MARGIN"
    FUTURES = "FUTURES"


@unique
class FinanceAccountType(StrEnum):
    BINANCE = "BINANCE"
    BYBIT = "BYBIT"
