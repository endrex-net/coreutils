from enum import StrEnum, unique


@unique
class WalletType(StrEnum):
    SPOT = "SPOT"
    MARGIN = "MARGIN"
    FUTURES = "FUTURES"
