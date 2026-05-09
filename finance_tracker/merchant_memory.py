"""
Persistent merchant memory for learned categorizations.

Stores and retrieves learned merchant-to-category mappings from JSON.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

from .constants import MERCHANT_MEMORY_FILE, MERCHANT_MEMORY_DIR
from .normalizer import normalize_merchant_name

logger = logging.getLogger(__name__)


class MerchantMemory:
    """
    Manages persistent storage of merchant-to-category mappings.

    Learns from categorized transactions and recalls learned merchants
    to improve and speed up future categorization.
    """

    def __init__(self, memory_file: str = MERCHANT_MEMORY_FILE):
        """
        Initialize merchant memory.

        Args:
            memory_file: Path to JSON file storing merchant mappings.
        """
        self.memory_file = Path(memory_file)
        self.memory_dir = Path(MERCHANT_MEMORY_DIR)
        self._memory: Dict[str, str] = {}
        self._load_memory()

    def _load_memory(self) -> None:
        """Load merchant mappings from JSON file."""
        try:
            if self.memory_file.exists():
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    self._memory = json.load(f)
                logger.debug(
                    f"Loaded {len(self._memory)} merchants from {self.memory_file}"
                )
            else:
                self._memory = {}
                logger.debug(
                    f"Merchant memory file not found: {self.memory_file}"
                )
        except Exception as e:
            logger.warning(f"Failed to load merchant memory: {e}")
            self._memory = {}

    def _save_memory(self) -> None:
        """Save merchant mappings to JSON file."""
        try:
            self.memory_dir.mkdir(parents=True, exist_ok=True)
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self._memory, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved merchant memory to {self.memory_file}")
        except Exception as e:
            logger.error(f"Failed to save merchant memory: {e}")

    def get(self, merchant: str) -> Optional[str]:
        """
        Retrieve learned category for a merchant.

        Args:
            merchant: Merchant name (will be normalized).

        Returns:
            Learned category if found, None otherwise.
        """
        normalized = normalize_merchant_name(merchant)
        return self._memory.get(normalized)

    def learn(self, merchant: str, category: str) -> None:
        """
        Learn a merchant-to-category mapping.

        Args:
            merchant: Merchant name (will be normalized).
            category: Category to associate with merchant.
        """
        normalized = normalize_merchant_name(merchant)
        if not normalized:
            logger.warning(f"Cannot learn empty merchant name: '{merchant}'")
            return

        if normalized not in self._memory or self._memory[normalized] != category:
            self._memory[normalized] = category
            self._save_memory()
            logger.debug(f"Learned: {normalized} -> {category}")

    def learn_batch(self, merchant_category_pairs: Dict[str, str]) -> None:
        """
        Learn multiple merchant-to-category mappings.

        Args:
            merchant_category_pairs: Dictionary of merchant -> category mappings.
        """
        for merchant, category in merchant_category_pairs.items():
            self.learn(merchant, category)

    def has_merchant(self, merchant: str) -> bool:
        """
        Check if a merchant is in memory.

        Args:
            merchant: Merchant name (will be normalized).

        Returns:
            True if merchant is in memory, False otherwise.
        """
        normalized = normalize_merchant_name(merchant)
        return normalized in self._memory

    def get_all(self) -> Dict[str, str]:
        """
        Get all learned merchant mappings.

        Returns:
            Dictionary of all merchant -> category mappings.
        """
        return self._memory.copy()

    def size(self) -> int:
        """
        Get the number of learned merchants.

        Returns:
            Count of merchants in memory.
        """
        return len(self._memory)

    def clear(self) -> None:
        """Clear all merchant memory and delete file."""
        self._memory = {}
        if self.memory_file.exists():
            try:
                self.memory_file.unlink()
                logger.debug(f"Cleared merchant memory")
            except Exception as e:
                logger.error(f"Failed to delete merchant memory file: {e}")
