from enum import StrEnum, unique


@unique
class ProfileType(StrEnum):
    CLIENT = "CLIENT"
    TRADER = "TRADER"
