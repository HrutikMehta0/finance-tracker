"""
Core data models for the finance tracker application.
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Transaction:
    """
    Represents a single financial transaction.

    Attributes:
        date: Transaction date and time.
        name: Merchant or description of the transaction.
        category: Category classification of the transaction.
        spent_from: Account from which the transaction was made.
        amount: Transaction amount (in currency units, typically dollars).
        notes: Additional notes or metadata about the transaction.
        transaction_id: Unique identifier for the transaction (usually a hash).
    """

    date: datetime
    name: str
    category: str
    spent_from: str
    amount: float
    notes: str
    transaction_id: str