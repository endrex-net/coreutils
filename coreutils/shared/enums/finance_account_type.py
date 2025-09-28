from enum import StrEnum, unique


@unique
class FinanceAccountType(StrEnum):
    BINANCE = "BINANCE"
    BYBIT = "BYBIT"
