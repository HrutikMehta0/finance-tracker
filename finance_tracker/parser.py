"""
CSV file parsing for bank transaction data.

Provides utilities to parse RBC bank CSV files and normalize transaction data
into a standard DataFrame format.
"""
import logging
import pdfplumber
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

from .deduplicator import add_transaction_id_column
from .models import Transaction
from .normalizer import normalize_column_name, normalize_description

logger = logging.getLogger(__name__)


def transactions_from_df(df: pd.DataFrame) -> List[Transaction]:
    """
    Convert a DataFrame to a list of Transaction objects.

    Args:
        df: DataFrame with columns: date, description, amount, account, category, transaction_id.

    Returns:
        List of Transaction objects.

    Raises:
        ValueError: If required columns are missing.
    """
    required_cols = [
        "date",
        "description",
        "amount",
        "account",
        "category",
        "transaction_id",
    ]

    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"DataFrame missing required columns: {missing_cols}")

    transactions = []
    for _, row in df.iterrows():
        txn = Transaction(
            date=pd.Timestamp(row["date"]).to_pydatetime(),
            name=str(row["description"]),
            category=str(row.get("category", "Uncategorized")),
            spent_from=str(row["account"]),
            amount=float(row["amount"]),
            notes=str(row.get("notes", "")),
            transaction_id=str(row["transaction_id"]),
        )
        transactions.append(txn)

    logger.debug(f"Created {len(transactions)} Transaction objects from DataFrame")
    return transactions



def detect_csv_structure(file_path: str) -> Dict[str, str]:
    """
    Detect the structure of a CSV file to identify column mappings.

    Reads the first row of the CSV and identifies common column patterns
    for bank transaction files.

    Args:
        file_path: Path to CSV file.

    Returns:
        Dictionary mapping standard columns to actual CSV column names.
        Examples: {'date': 'Transaction Date', 'amount': 'CAD$', ...}

    Raises:
        FileNotFoundError: If file doesn't exist.
        ValueError: If CSV structure cannot be determined.
    """
    csv_path = Path(file_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    try:
        df = pd.read_csv(file_path, nrows=1)
        columns = df.columns.tolist()

        structure = {}

        # Detect date column
        date_patterns = ["transaction date", "date", "posted date"]
        for col in columns:
            col_lower = col.lower()
            if any(pattern in col_lower for pattern in date_patterns):
                structure["date"] = col
                break

        # Detect description columns
        desc_patterns = [
            "description",
            "merchant",
            "payee",
            "reference",
        ]
        desc_cols = []
        for col in columns:
            col_lower = col.lower()
            if any(pattern in col_lower for pattern in desc_patterns):
                desc_cols.append(col)
        if desc_cols:
            structure["description"] = desc_cols

        # Detect amount column
        amount_patterns = ["cad\\$", "usd\\$", "amount", "transaction amount"]
        for col in columns:
            col_lower = col.lower()
            if any(pattern in col_lower for pattern in amount_patterns):
                structure["amount"] = col
                break

        logger.debug(f"Detected CSV structure: {structure}")
        return structure

    except Exception as e:
        logger.error(f"Failed to detect CSV structure: {e}")
        raise ValueError(f"Cannot determine CSV structure: {e}")


def parse_rbc_csv(file_path: str, account: str) -> pd.DataFrame:
    """
    Parse an RBC bank CSV export file and normalize to standard format.

    Handles flexible RBC CSV formats, normalizing columns and extracting
    transaction data. Does NOT perform categorization - use Categorizer
    for that functionality.

    Args:
        file_path: Path to RBC CSV file.
        account: Account name or identifier (e.g., 'chequing', 'savings').

    Returns:
        DataFrame with columns: date, description, amount, account, transaction_id
        All data is normalized and deduplicated.

    Raises:
        FileNotFoundError: If file doesn't exist.
        ValueError: If file cannot be parsed.
    """
    logger.info(f"Parsing RBC CSV: {file_path}")

    csv_path = Path(file_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    try:
        # Read CSV with flexible handling
        df = pd.read_csv(file_path)

        # Normalize column names for easier processing
        df.columns = [normalize_column_name(col) for col in df.columns]

        # Extract description from one or more columns
        description_col = _extract_description(df)
        if not description_col:
            raise ValueError("Cannot find description column in CSV")

        # Extract amount from one or more columns
        amount_col = _extract_amount(df)
        if not amount_col:
            raise ValueError("Cannot find amount column in CSV")

        # Extract date
        date_col = _extract_date(df)
        if not date_col:
            raise ValueError("Cannot find date column in CSV")

        # Normalize description data
        df["description"] = (
            df[description_col]
            .fillna("")
            .astype(str)
            .apply(normalize_description)
        )

        # Normalize amount to float
        df["amount"] = pd.to_numeric(
            df[amount_col]
            .astype(str)
            .str.replace("$", "", regex=False)
            .str.replace(",", "", regex=False),
            errors="coerce",
        ).fillna(0.0)

        # Parse date
        df["date"] = pd.to_datetime(df[date_col], errors="coerce")

        # Add account identifier
        df["account"] = account

        # Add transaction IDs
        df = add_transaction_id_column(df)

        # Select and return normalized subset
        result_df = df[["date", "description", "amount", "account", "transaction_id"]].copy()

        logger.info(f"Parsed {len(result_df)} transactions from RBC CSV")
        return result_df

    except Exception as e:
        logger.error(f"Failed to parse RBC CSV: {e}")
        raise


def _extract_description(df: pd.DataFrame) -> Optional[str]:
    """
    Find and return the description column name from DataFrame.

    Args:
        df: DataFrame with normalized column names.

    Returns:
        Column name containing description, or None if not found.
    """
    patterns = ["description", "merchant", "payee", "reference"]

    for col in df.columns:
        col_lower = col.lower()
        if any(pattern in col_lower for pattern in patterns):
            return col

    # Fallback: use first string column
    for col in df.columns:
        if df[col].dtype == "object":
            return col

    return None


def _extract_amount(df: pd.DataFrame) -> Optional[str]:
    """
    Find and return the amount column name from DataFrame.

    Args:
        df: DataFrame with normalized column names.

    Returns:
        Column name containing amount, or None if not found.
    """
    patterns = ["amount", "cad", "usd", "transaction", "total"]

    for col in df.columns:
        col_lower = col.lower()
        if any(pattern in col_lower for pattern in patterns):
            return col

    return None


def _extract_date(df: pd.DataFrame) -> Optional[str]:
    """
    Find and return the date column name from DataFrame.

    Args:
        df: DataFrame with normalized column names.

    Returns:
        Column name containing date, or None if not found.
    """
    patterns = ["date", "posted", "transaction"]

    for col in df.columns:
        col_lower = col.lower()
        if any(pattern in col_lower for pattern in patterns):
            return col

    return None

def detect_file_type(file_path: str) -> str:
    """Return the detected file type: 'csv' or 'pdf' or 'excel'."""
    p = Path(file_path)
    suffix = p.suffix.lower()
    if suffix in {".csv"}:
        return "csv"
    if suffix in {".pdf"}:
        return "pdf"
    if suffix in {".xls", ".xlsx"}:
        return "excel"
    # Fallback: try to inspect file header
    try:
        with open(p, "rb") as fh:
            header = fh.read(8)
            if header.startswith(b"%PDF"):
                return "pdf"
    except Exception:
        pass
    return "unknown"


def parse_rbc_pdf(file_path: str, account: str) -> pd.DataFrame:
    """
    Parse an RBC PDF statement into a normalized DataFrame.

    This is a best-effort parser: it tries to extract tabular transaction rows
    from the PDF using pdfplumber. If table extraction fails, it falls back to
    line-based regex extraction.
    """
    logger.info(f"Parsing RBC PDF: {file_path}")
    pdf_path = Path(file_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    rows: List[Tuple[str, str, float]] = []

    date_re = re.compile(r"(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-[A-Za-z]{3}-\d{2})")
    amount_re = re.compile(r"-?\$?\s?([0-9,]+\.?[0-9]{0,2})$")

    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page in pdf.pages:
                # Try table extraction first
                try:
                    tables = page.extract_tables()
                except Exception:
                    tables = []

                if tables:
                    for table in tables:
                        for row in table:
                            # row is list of cells; try to find date, desc, amount
                            if not row:
                                continue
                            row_text = [str(c).strip() if c is not None else "" for c in row]
                            joined = " | ".join(row_text)
                            mdate = date_re.search(joined)
                            mamount = amount_re.search(joined)
                            if mdate and mamount:
                                date = mdate.group(0)
                                amount = float(mamount.group(1).replace(",", ""))
                                # description is middle content
                                desc_parts = [c for c in row_text if c and c != mdate.group(0) and c != mamount.group(1)]
                                description = " ".join(desc_parts).strip()
                                rows.append((date, description, amount))
                else:
                    # Fallback: line-based
                    text = page.extract_text() or ""
                    for line in text.splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        mdate = date_re.search(line)
                        mamount = amount_re.search(line)
                        if mdate and mamount:
                            date = mdate.group(0)
                            amount = float(mamount.group(1).replace(",", ""))
                            # take middle part as description
                            description = line[mdate.end():mamount.start()].strip(" -|,")
                            rows.append((date, description, amount))

        # Build DataFrame
        df = pd.DataFrame(rows, columns=["date", "description", "amount"])
        if df.empty:
            logger.warning(f"No transactions found in PDF: {file_path}")
        else:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df["description"] = df["description"].fillna("").astype(str)
            df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
            df["account"] = account

            # Add transaction IDs
            df = add_transaction_id_column(df)

            df = df[["date", "description", "amount", "account", "transaction_id"]]

        logger.info(f"Parsed {len(df)} transactions from RBC PDF")
        return df
    except Exception as e:
        logger.error(f"Failed to parse RBC PDF: {e}")
        raise


def parse_statement(file_path: str, account: str) -> pd.DataFrame:
    """Auto-detect statement type (CSV/PDF/Excel) and parse into normalized DataFrame."""
    ftype = detect_file_type(file_path)
    if ftype == "csv":
        return parse_rbc_csv(file_path, account)
    if ftype == "pdf":
        return parse_rbc_pdf(file_path, account)
    if ftype == "excel":
        # For now, try pandas.read_excel and map to same format
        logger.info(f"Parsing Excel workbook or sheet: {file_path}")
        try:
            df = pd.read_excel(file_path)
            df.columns = [c for c in df.columns]
            # Attempt to normalize via existing CSV path
            df.columns = [normalize_column_name(col) for col in df.columns]
            description_col = _extract_description(df)
            amount_col = _extract_amount(df)
            date_col = _extract_date(df)
            df["description"] = df[description_col].fillna("").astype(str).apply(normalize_description)
            df["amount"] = pd.to_numeric(df[amount_col], errors="coerce").fillna(0.0)
            df["date"] = pd.to_datetime(df[date_col], errors="coerce")
            df["account"] = account
            df = add_transaction_id_column(df)
            return df[["date", "description", "amount", "account", "transaction_id"]]
        except Exception as e:
            logger.error(f"Failed to parse Excel statement: {e}")
            raise

    raise ValueError(f"Unsupported or unknown file type for parsing: {file_path}")
