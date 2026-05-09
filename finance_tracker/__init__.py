"""
Finance Tracker - A modular transaction parsing and categorization library.

Provides utilities for parsing bank CSV exports, categorizing transactions,
and exporting to various formats with intelligent merchant memory and fuzzy matching.
"""

from .categorizer import Categorizer
from .config_loader import ConfigLoader
from .exporter import Exporter
from .merchant_memory import MerchantMemory
from .models import Transaction
from .file_tracker import FileTracker
from .logging_config import configure_logging, get_logger
from .normalizer import (
    extract_merchant_from_description,
    normalize_column_name,
    normalize_description,
    normalize_merchant_name,
)
from .parser import parse_rbc_csv, transactions_from_df
from .deduplicator import (
    add_transaction_id_column,
    find_duplicate_transactions,
    generate_transaction_hash,
    remove_duplicate_transactions,
)

__version__ = "2.0.0"

__all__ = [
    "Categorizer",
    "ConfigLoader",
    "Exporter",
    "MerchantMemory",
    "FileTracker",
    "Transaction",
    "configure_logging",
    "get_logger",
    "normalize_merchant_name",
    "normalize_description",
    "normalize_column_name",
    "extract_merchant_from_description",
    "parse_rbc_csv",
    "transactions_from_df",
    "add_transaction_id_column",
    "generate_transaction_hash",
    "find_duplicate_transactions",
    "remove_duplicate_transactions",
]
