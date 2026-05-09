"""Unit tests for the normalizer module."""
import unittest

from finance_tracker.normalizer import (
    extract_merchant_from_description,
    normalize_column_name,
    normalize_description,
    normalize_merchant_name,
)


class TestNormalizer(unittest.TestCase):
    """Tests for text normalization functions."""

    def test_normalize_merchant_name(self):
        """Test merchant name normalization."""
        # Branch number removal
        self.assertEqual(
            normalize_merchant_name("TIM HORTONS #4432"), "Tim Hortons"
        )

        # Multiple spaces
        self.assertEqual(
            normalize_merchant_name("WALMART  SUPERCENTRE"), "Walmart Supercentre"
        )

        # Title case conversion
        self.assertEqual(normalize_merchant_name("starbucks coffee"), "Starbucks Coffee")

        # Empty/None
        self.assertEqual(normalize_merchant_name(""), "")
        self.assertEqual(normalize_merchant_name(None), "")

    def test_normalize_description(self):
        """Test description normalization."""
        # Lowercase and special character removal
        self.assertEqual(
            normalize_description("STARBUCKS COFFEE #123"),
            "starbucks coffee 123",
        )

        # Multiple spaces collapsed
        self.assertEqual(
            normalize_description("RESTAURANT  &  BAR"), "restaurant bar"
        )

        # Empty/None
        self.assertEqual(normalize_description(""), "")
        self.assertEqual(normalize_description(None), "")

    def test_normalize_column_name(self):
        """Test column name normalization."""
        # Spaces to underscores
        self.assertEqual(normalize_column_name("Transaction Date"), "transaction_date")

        # Special characters removed
        self.assertEqual(normalize_column_name("CAD$"), "cad")

        # Multiple underscores collapsed
        self.assertEqual(
            normalize_column_name("Amount  In  Dollars"), "amount_in_dollars"
        )

        # Empty/None
        self.assertEqual(normalize_column_name(""), "")
        self.assertEqual(normalize_column_name(None), "")

    def test_extract_merchant_from_description(self):
        """Test merchant extraction from description."""
        # Extract primary merchant
        self.assertEqual(
            extract_merchant_from_description("TIM HORTONS 456 MAIN ST"),
            "Tim Hortons",
        )

        # Empty description
        self.assertEqual(extract_merchant_from_description(""), "")

        # None
        self.assertEqual(extract_merchant_from_description(None), "")


if __name__ == "__main__":
    unittest.main()
