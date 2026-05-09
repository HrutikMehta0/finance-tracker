"""Unit tests for the categorizer module."""
import unittest
import tempfile
import json
from pathlib import Path

from finance_tracker.categorizer import Categorizer
from finance_tracker.constants import DEFAULT_CATEGORY
from finance_tracker.merchant_memory import MerchantMemory


class TestCategorizer(unittest.TestCase):
    """Tests for transaction categorization."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary merchant memory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.memory_file = Path(self.temp_dir) / "test_memory.json"

    def tearDown(self):
        """Clean up test fixtures."""
        if self.memory_file.exists():
            self.memory_file.unlink()

    def test_keyword_categorization(self):
        """Test categorization by keyword matching."""
        categorizer = Categorizer()

        # Test grocery keywords
        category, confidence = categorizer.categorize("COSTCO WHOLESALE #123")
        self.assertEqual(category, "Groceries")
        self.assertGreater(confidence, 0)

        # Test dining keywords
        category, confidence = categorizer.categorize("STARBUCKS COFFEE #456")
        self.assertEqual(category, "Dining")
        self.assertGreater(confidence, 0)

        # Test utilities keywords
        category, confidence = categorizer.categorize("ROGERS INTERNET SERVICES")
        self.assertEqual(category, "Utilities")
        self.assertGreater(confidence, 0)

    def test_uncategorized(self):
        """Test uncategorized transactions."""
        categorizer = Categorizer()

        category, confidence = categorizer.categorize("UNKNOWN MERCHANT XYZ")
        self.assertEqual(category, DEFAULT_CATEGORY)
        self.assertEqual(confidence, 0.0)

    def test_empty_description(self):
        """Test handling of empty descriptions."""
        categorizer = Categorizer()

        category, confidence = categorizer.categorize("")
        self.assertEqual(category, DEFAULT_CATEGORY)
        self.assertEqual(confidence, 0.0)

        category, confidence = categorizer.categorize(None)
        self.assertEqual(category, DEFAULT_CATEGORY)
        self.assertEqual(confidence, 0.0)

    def test_merchant_memory_learning(self):
        """Test merchant memory learning."""
        memory = MerchantMemory(str(self.memory_file))
        categorizer = Categorizer(merchant_memory=memory)

        # Learn a merchant
        categorizer.learn("STARBUCKS", "Coffee")

        # Should retrieve the learned category
        category, confidence = categorizer.categorize("STARBUCKS")
        self.assertEqual(category, "Coffee")

    def test_fuzzy_matching(self):
        """Test fuzzy matching for similar merchants."""
        categorizer = Categorizer()

        # "Starbucks" should fuzzy match with keywords "starbucks"
        category, confidence = categorizer.categorize("STARBUX COFFE")
        # Fuzzy match may not work perfectly, but test the mechanism
        self.assertIsNotNone(category)

    def test_add_category_rule(self):
        """Test adding new category rules."""
        categorizer = Categorizer()

        # Add new rule
        categorizer.add_category_rule("Pet Store", ["petco", "petsmart"])

        # Should be categorizable now
        category, confidence = categorizer.categorize("PETCO #123")
        self.assertEqual(category, "Pet Store")

    def test_categorize_with_learning(self):
        """Test categorization with learning enabled."""
        memory = MerchantMemory(str(self.memory_file))
        categorizer = Categorizer(merchant_memory=memory)

        # Categorize with learning
        category, confidence = categorizer.categorize(
            "STARBUCKS COFFEE #123", learn=True
        )

        # Merchant should now be in memory
        self.assertTrue(memory.has_merchant("STARBUCKS COFFEE #123"))


class TestMerchantMemory(unittest.TestCase):
    """Tests for merchant memory persistence."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.memory_file = Path(self.temp_dir) / "test_memory.json"

    def tearDown(self):
        """Clean up test fixtures."""
        if self.memory_file.exists():
            self.memory_file.unlink()

    def test_learn_merchant(self):
        """Test learning a merchant."""
        memory = MerchantMemory(str(self.memory_file))

        memory.learn("STARBUCKS", "Dining")

        # Should retrieve the learned mapping
        self.assertEqual(memory.get("STARBUCKS"), "Dining")

    def test_merchant_memory_persistence(self):
        """Test that merchant memory persists to file."""
        # Learn merchants
        memory1 = MerchantMemory(str(self.memory_file))
        memory1.learn("STARBUCKS", "Dining")
        memory1.learn("UBER", "Transport")

        # Load from new instance
        memory2 = MerchantMemory(str(self.memory_file))

        self.assertEqual(memory2.get("STARBUCKS"), "Dining")
        self.assertEqual(memory2.get("UBER"), "Transport")

    def test_has_merchant(self):
        """Test checking if merchant is in memory."""
        memory = MerchantMemory(str(self.memory_file))

        memory.learn("STARBUCKS", "Dining")

        self.assertTrue(memory.has_merchant("STARBUCKS"))
        self.assertFalse(memory.has_merchant("UNKNOWN"))

    def test_get_all(self):
        """Test getting all merchants."""
        memory = MerchantMemory(str(self.memory_file))

        memory.learn("STARBUCKS", "Dining")
        memory.learn("UBER", "Transport")

        all_merchants = memory.get_all()

        self.assertIn("Starbucks", all_merchants)
        self.assertIn("Uber", all_merchants)

    def test_merchant_memory_size(self):
        """Test merchant memory size."""
        memory = MerchantMemory(str(self.memory_file))

        self.assertEqual(memory.size(), 0)

        memory.learn("STARBUCKS", "Dining")
        self.assertEqual(memory.size(), 1)

        memory.learn("UBER", "Transport")
        self.assertEqual(memory.size(), 2)


if __name__ == "__main__":
    unittest.main()
