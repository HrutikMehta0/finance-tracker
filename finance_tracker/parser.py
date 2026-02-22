import re
import hashlib
from datetime import datetime
from typing import List

import pandas as pd

from .models import Transaction


def categorize_description(description: str) -> str:
    """Return a category label based on keywords found in the description.

    This uses simple, maintainable keyword heuristics. Add or tweak
    keywords as needed for better accuracy.
    """
    if not description:
        return "Uncategorized"

    desc = re.sub(r"[^a-z0-9\s]", " ", description.lower())

    rules = [
        ("Groceries", ["grocery", "market", "supermarket", "sobeys", "loblaws", "costco", "walmart"]),
        ("Rent", ["rent", "lease", "landlord"]),
        ("Utilities", ["hydro", "electricity", "water", "gas bill", "telus", "rogers", "bell", "internet", "freedom mobile"]),
        ("Dining", ["restaurant", "cafe", "coffee", "starbucks", "tim hortons", "timhortons", "mcdonald", "burger", "ubereats", "uber eats", "doordash", "grubhub", "pizza"]),
        ("Transport", ["uber", "lyft", "taxi", "parking", "fuel", "gas station", "transit", "bus", "train", "compass", "compass account", "compass card"]),
        ("Salary", ["payroll", "salary", "pay cheque", "direct deposit", "deposit"]),
        ("Transfer", ["transfer", "interac", "e-transfer", "eft"]),
        ("Entertainment", ["netflix", "spotify", "movie", "cinema", "theatre", "concert"]),
        ("Healthcare", ["pharmacy", "drug", "hospital", "clinic", "doctor", "dentist"]),
        ("Subscription", ["subscription", "membership", "monthly fee"]),
        ("Insurance", ["insurance"]),
        ("ATM/Cash", ["atm", "cash"]),
        ("Interest/Fees", ["interest", "fee", "service charge"]),
        ("Fitness", ["gym", "fitness", "evolve strength post", "evolve strength", "evolve"]),
        ("Avoidable Expenses", [
            "vapezilla smoke shop",
            "the blarney stone",
            "the portside pub",
            "viti wine and lager",
        ]),
    ]

    for category, keywords in rules:
        for kw in keywords:
            if kw in desc:
                return category

    return "Uncategorized"


def _make_transaction_id(row: pd.Series) -> str:
    key = f"{row.get('Date')}-{row.get('Description')}-{row.get('Amount')}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()


def parse_rbc_csv(file_path: str, account: str) -> pd.DataFrame:
    """Parse an RBC-style CSV and add normalized columns including `Category`.

    Returns a DataFrame with at least: `Date`, `Description`, `Amount`, `Account`, `Category`, `Transaction ID`.
    """
    df = pd.read_csv(file_path)

    # Build a single description field from the two description columns if present
    if "Description 1" in df.columns or "Description 2" in df.columns:
        d1 = df.get("Description 1") if "Description 1" in df.columns else ""
        d2 = df.get("Description 2") if "Description 2" in df.columns else ""
        df["Description"] = (d1.fillna("") + " " + d2.fillna("")).str.strip()
    elif "Description" not in df.columns:
        df["Description"] = ""

    # Determine amount column and coerce to numeric
    if "CAD$" in df.columns:
        amt_col = "CAD$"
    elif "USD$" in df.columns:
        amt_col = "USD$"
    else:
        amt_col = "Amount" if "Amount" in df.columns else None

    if amt_col:
        df["Amount"] = pd.to_numeric(df[amt_col].astype(str).str.replace("$", "", regex=False).str.replace(",", ""), errors="coerce").fillna(0.0)
    else:
        df["Amount"] = 0.0

    # Parse date column
    if "Transaction Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Transaction Date"], errors="coerce")
    elif "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    else:
        df["Date"] = pd.NaT

    df["Account"] = account
    df["Category"] = df["Description"].fillna("").apply(categorize_description)
    df["Transaction ID"] = df.apply(_make_transaction_id, axis=1)

    return df[["Date", "Description", "Amount", "Account", "Category", "Transaction ID"]]


def transactions_from_df(df: pd.DataFrame) -> List[Transaction]:
    """Convert a parsed DataFrame into a list of `Transaction` objects."""
    transactions: List[Transaction] = []
    for _, row in df.iterrows():
        t = Transaction(
            date=row.get("Date"),
            name=row.get("Description", ""),
            category=row.get("Category", "Uncategorized"),
            spent_from=row.get("Account", ""),
            amount=float(row.get("Amount") or 0.0),
            notes="",
            transaction_id=row.get("Transaction ID", _make_transaction_id(row)),
        )
        transactions.append(t)

    return transactions

def export_transactions_to_xlsx(transactions: List[Transaction], output_path: str) -> None:
    """Export a list of `Transaction` objects to an Excel file."""
    df = pd.DataFrame([t.__dict__ for t in transactions])
    df.to_excel(output_path, index=False)