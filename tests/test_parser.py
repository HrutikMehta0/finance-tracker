"""
Parser module tests.

Tests for CSV parsing and transaction data normalization.
"""
import unittest
import tempfile
from pathlib import Path
from datetime import datetime

import pandas as pd

from finance_tracker.parser import parse_rbc_csv, transactions_from_df


class TestParser(unittest.TestCase):
    """Tests for CSV parsing."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def test_transactions_from_df(self):
        """Test converting DataFrame to Transaction objects."""
        data = {
            "date": pd.to_datetime(["2024-01-15", "2024-01-16"]),
            "description": ["STARBUCKS", "WALMART"],
            "amount": [5.5, 25.0],
            "account": ["chequing", "chequing"],
            "category": ["Dining", "Groceries"],
            "transaction_id": ["hash1", "hash2"],
        }
        df = pd.DataFrame(data)

        transactions = transactions_from_df(df)

        self.assertEqual(len(transactions), 2)
        self.assertEqual(transactions[0].name, "STARBUCKS")
        self.assertEqual(transactions[0].amount, 5.5)
        self.assertEqual(transactions[1].category, "Groceries")

    def test_transactions_from_df_missing_columns(self):
        """Test error when required columns are missing."""
        data = {"description": ["STARBUCKS"], "amount": [5.5]}
        df = pd.DataFrame(data)

        with self.assertRaises(ValueError):
            transactions_from_df(df)


if __name__ == "__main__":
    unittest.main()
