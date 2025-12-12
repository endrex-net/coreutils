from typing import NewType
from uuid import UUID


UserId = NewType("UserId", UUID)
WalletId = NewType("WalletId", UUID)
FinanceAccountId = NewType("FinanceAccountId", UUID)
ExchangeId = NewType("ExchangeId", int)
