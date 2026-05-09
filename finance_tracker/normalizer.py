"""
Text normalization utilities for merchants and transactions.

Provides functions to normalize merchant descriptions and column names
for consistent processing and deduplication.
"""
import re
from typing import Dict, List


def normalize_merchant_name(merchant: str) -> str:
    """
    Normalize a merchant description to a canonical form.

    Removes branch numbers, extra whitespace, and converts to title case.
    
    Examples:
        "TIM HORTONS #4432" -> "Tim Hortons"
        "STARBUCKS COFFEE  #123" -> "Starbucks Coffee"
        "walmart supercentre" -> "Walmart Supercentre"

    Args:
        merchant: Raw merchant description from transaction.

    Returns:
        Normalized merchant name in title case.
    """
    if not merchant or not isinstance(merchant, str):
        return ""

    # Remove branch numbers (e.g., #4432, #123)
    normalized = re.sub(r"\s*#\d+\s*", "", merchant)

    # Remove extra whitespace
    normalized = " ".join(normalized.split())

    # Convert to title case
    normalized = normalized.title()

    return normalized.strip()


def normalize_description(description: str) -> str:
    """
    Normalize a transaction description for categorization.

    Converts to lowercase, removes special characters, keeps only alphanumeric and spaces.

    Args:
        description: Raw transaction description.

    Returns:
        Normalized description in lowercase with only alphanumeric characters.
    """
    if not description or not isinstance(description, str):
        return ""

    # Convert to lowercase
    normalized = description.lower()

    # Remove special characters, keep only alphanumeric and spaces
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)

    # Remove extra whitespace
    normalized = " ".join(normalized.split())

    return normalized.strip()


def normalize_column_name(column: str) -> str:
    """
    Normalize a DataFrame column name to a standard format.

    Converts to lowercase with underscores instead of spaces.

    Args:
        column: Raw column name.

    Returns:
        Normalized column name (lowercase with underscores).
    """
    if not column or not isinstance(column, str):
        return ""

    # Convert to lowercase
    normalized = column.lower()

    # Replace spaces and special characters with underscores
    normalized = re.sub(r"[\s\-]+", "_", normalized)
    normalized = re.sub(r"[^a-z0-9_]", "", normalized)

    # Remove leading/trailing underscores and collapse multiple underscores
    normalized = re.sub(r"_+", "_", normalized).strip("_")

    return normalized


def extract_merchant_from_description(description: str) -> str:
    """
    Extract the merchant name from a transaction description.

    Attempts to extract the primary merchant name from descriptions
    that may contain additional information.

    Args:
        description: Transaction description, possibly containing merchant and location.

    Returns:
        Extracted merchant name.
    """
    if not description:
        return ""

    # Split by common delimiters
    parts = re.split(r"\s+\d+\s+", description)
    merchant = parts[0].strip()

    return normalize_merchant_name(merchant)
