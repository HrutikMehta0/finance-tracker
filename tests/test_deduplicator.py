"""Unit tests for the deduplicator module."""
import unittest
from datetime import datetime

import pandas as pd

from finance_tracker.deduplicator import (
    add_transaction_id_column,
    find_duplicate_transactions,
    generate_transaction_hash,
    remove_duplicate_transactions,
)


class TestDeduplicator(unittest.TestCase):
    """Tests for transaction deduplication functions."""

    def test_generate_transaction_hash(self):
        """Test transaction hash generation."""
        date = datetime(2024, 1, 15)
        desc = "STARBUCKS COFFEE"
        amount = 5.50
        account = "chequing"

        hash1 = generate_transaction_hash(date, desc, amount, account)
        hash2 = generate_transaction_hash(date, desc, amount, account)

        # Same inputs should produce same hash
        self.assertEqual(hash1, hash2)

        # Different inputs should produce different hash
        hash3 = generate_transaction_hash(date, "DIFFERENT", amount, account)
        self.assertNotEqual(hash1, hash3)

    def test_generate_transaction_hash_with_string_date(self):
        """Test transaction hash generation with string date."""
        date_str = "2024-01-15"
        hash1 = generate_transaction_hash(date_str, "MERCHANT", 10.0)

        # Should handle string dates
        self.assertIsInstance(hash1, str)
        self.assertTrue(len(hash1) > 0)

    def test_add_transaction_id_column(self):
        """Test adding transaction ID column to DataFrame."""
        data = {
            "date": ["2024-01-15", "2024-01-16"],
            "description": ["STARBUCKS", "WALMART"],
            "amount": [5.5, 25.0],
            "account": ["chequing", "chequing"],
        }
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])

        result = add_transaction_id_column(df)

        # Should add transaction_id column
        self.assertIn("transaction_id", result.columns)

        # Should have same number of rows
        self.assertEqual(len(result), 2)

        # Transaction IDs should be unique for different transactions
        self.assertNotEqual(result.iloc[0]["transaction_id"], result.iloc[1]["transaction_id"])

    def test_add_transaction_id_column_missing_columns(self):
        """Test error when required columns are missing."""
        data = {"description": ["STARBUCKS"]}
        df = pd.DataFrame(data)

        with self.assertRaises(ValueError):
            add_transaction_id_column(df)

    def test_find_duplicate_transactions(self):
        """Test finding duplicate transactions."""
        data = {
            "date": ["2024-01-15", "2024-01-15", "2024-01-16"],
            "description": ["STARBUCKS", "STARBUCKS", "WALMART"],
            "amount": [5.5, 5.5, 25.0],
        }
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])

        duplicates = find_duplicate_transactions(df)

        # Should find 2 duplicate rows
        self.assertEqual(len(duplicates), 2)

    def test_remove_duplicate_transactions(self):
        """Test removing duplicate transactions."""
        data = {
            "date": ["2024-01-15", "2024-01-15", "2024-01-16"],
            "description": ["STARBUCKS", "STARBUCKS", "WALMART"],
            "amount": [5.5, 5.5, 25.0],
            "transaction_id": ["hash1", "hash1", "hash2"],
        }
        df = pd.DataFrame(data)

        result = remove_duplicate_transactions(df)

        # Should keep only first occurrence
        self.assertEqual(len(result), 2)

    def test_remove_duplicate_transactions_keep_last(self):
        """Test removing duplicates keeping last occurrence."""
        data = {
            "date": ["2024-01-15", "2024-01-15"],
            "description": ["STARBUCKS", "STARBUCKS"],
            "amount": [5.5, 5.5],
            "transaction_id": ["hash1", "hash1"],
        }
        df = pd.DataFrame(data)

        result = remove_duplicate_transactions(df, keep="last")

        # Should keep only last occurrence
        self.assertEqual(len(result), 1)


if __name__ == "__main__":
    unittest.main()
