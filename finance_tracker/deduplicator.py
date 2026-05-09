"""
Transaction deduplication utilities.

Provides hash generation and duplicate detection logic for transactions.
"""
import hashlib
from datetime import datetime
from typing import Optional

import pandas as pd

from .constants import HASH_ALGORITHM
from .normalizer import normalize_merchant_name


def generate_transaction_hash(
    date: datetime,
    description: str,
    amount: float,
    account: str = "",
) -> str:
    """
    Generate a unique hash for a transaction.

    Creates a deterministic hash from core transaction attributes
    to support duplicate detection.

    Args:
        date: Transaction date.
        description: Transaction description/merchant.
        amount: Transaction amount.
        account: Account name (optional, included in hash).

    Returns:
        Hex digest of transaction hash.
    """
    # Stable components: ISO date, normalized merchant, rounded amount (to cents), account
    date_part = (
        date.strftime("%Y-%m-%d") if isinstance(date, datetime) else str(date)
    )
    merchant_part = normalize_merchant_name(str(description))
    rounded_amount = f"{round(float(amount), 2):.2f}"
    key_parts = [date_part, merchant_part, rounded_amount, str(account).strip()]
    key = "-".join(key_parts)

    if HASH_ALGORITHM == "sha1":
        return hashlib.sha1(key.encode("utf-8")).hexdigest()
    elif HASH_ALGORITHM == "md5":
        return hashlib.md5(key.encode("utf-8")).hexdigest()
    else:
        return hashlib.sha256(key.encode("utf-8")).hexdigest()


def add_transaction_id_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a transaction ID column to a DataFrame.

    Generates a unique transaction ID for each row based on core attributes.

    Args:
        df: DataFrame with 'date', 'description', 'amount', and 'account' columns.

    Returns:
        DataFrame with added 'transaction_id' column.
    """
    df_copy = df.copy()

    if (
        "date" not in df_copy.columns
        or "description" not in df_copy.columns
        or "amount" not in df_copy.columns
    ):
        raise ValueError(
            "DataFrame must contain 'date', 'description', and 'amount' columns"
        )

    account = df_copy.get("account", [""] * len(df_copy))

    df_copy["transaction_id"] = df_copy.apply(
        lambda row: generate_transaction_hash(
            row["date"],
            row["description"],
            row["amount"],
            account[row.name] if isinstance(account, (list, pd.Series)) else account,
        ),
        axis=1,
    )

    return df_copy


def find_duplicate_transactions(
    df: pd.DataFrame,
    tolerance_cents: int = 0,
) -> pd.DataFrame:
    """
    Find potential duplicate transactions in a DataFrame.

    Identifies transactions with the same date, description, and similar amounts.

    Args:
        df: DataFrame with transaction data.
        tolerance_cents: Amount tolerance in cents (e.g., 5 for $0.05).

    Returns:
        DataFrame containing only potential duplicates, sorted by date and description.
    """
    if (
        "date" not in df.columns
        or "description" not in df.columns
        or "amount" not in df.columns
    ):
        return pd.DataFrame()

    # Group by date and description
    groups = df.groupby(["date", "description"]).size()

    # Filter groups with more than 1 transaction
    duplicates_groups = groups[groups > 1].index

    # Get duplicate rows
    is_duplicate = (
        df.set_index(["date", "description"]).index.isin(duplicates_groups)
    )
    duplicates = df[is_duplicate].sort_values(["date", "description"])

    return duplicates


def remove_duplicate_transactions(
    df: pd.DataFrame,
    keep: str = "first",
) -> pd.DataFrame:
    """
    Remove duplicate transactions from a DataFrame.

    Removes rows with identical date, description, and amount.

    Args:
        df: DataFrame with transaction data.
        keep: Which duplicate to keep: 'first', 'last', or False (remove all).

    Returns:
        DataFrame with duplicates removed.
    """
    if "transaction_id" in df.columns:
        return df.drop_duplicates(subset=["transaction_id"], keep=keep)

    return df.drop_duplicates(
        subset=["date", "description", "amount"],
        keep=keep,
    )
