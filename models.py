from dataclasses import dataclass
from datetime import datetime

@dataclass
class Customer:
    id: str
    name: str
    email: str

@dataclass
class Account:
    id: str
    customer_id: str
    type: str  # "current" or "savings"
    balance: float
    created_at: datetime

@dataclass
class Transaction:
    id: str
    account_id: str
    customer_id: str
    type: str  # "transfer", "payment", "bonus", "interest", "fee"
    amount: float
    created_at: datetime
    from_account_id: str | None = None
    to_account_id: str | None = None
