from dataclasses import dataclass
from datetime import datetime


@dataclass
class Transaction:
    date: datetime
    name: str
    category: str
    spent_from: str
    amount: float
    notes: str
    transaction_id: str