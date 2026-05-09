"""
Transaction categorization engine.

Categorizes transactions using multiple strategies:
1. Exact merchant memory match
2. Fuzzy matching on normalized merchants
3. Keyword-based rules fallback
"""
import logging
from typing import Dict, List, Optional, Tuple

from rapidfuzz import fuzz

from .constants import (
    CATEGORY_CONFIDENCE_HIGH,
    CATEGORY_CONFIDENCE_LOW,
    CATEGORY_CONFIDENCE_MEDIUM,
    DEFAULT_CATEGORY,
    FUZZY_MATCH_THRESHOLD,
)
from .merchant_memory import MerchantMemory
from .normalizer import normalize_description, normalize_merchant_name

logger = logging.getLogger(__name__)


class Categorizer:
    """
    Intelligent transaction categorizer with multiple strategies.

    Uses merchant memory, fuzzy matching, and keyword rules to categorize
    transactions with confidence scores.
    """

    # Default category rules with keywords
    DEFAULT_RULES: Dict[str, List[str]] = {
        "Groceries": [
            "grocery",
            "market",
            "supermarket",
            "sobeys",
            "loblaws",
            "costco",
            "walmart",
        ],
        "Rent": ["rent", "lease", "landlord"],
        "Utilities": [
            "hydro",
            "electricity",
            "water",
            "gas bill",
            "telus",
            "rogers",
            "bell",
            "internet",
            "freedom mobile",
        ],
        "Dining": [
            "restaurant",
            "cafe",
            "coffee",
            "starbucks",
            "tim hortons",
            "timhortons",
            "mcdonald",
            "burger",
            "ubereats",
            "uber eats",
            "doordash",
            "grubhub",
            "pizza",
        ],
        "Transport": [
            "uber",
            "lyft",
            "taxi",
            "parking",
            "fuel",
            "gas station",
            "transit",
            "bus",
            "train",
            "compass",
            "compass account",
            "compass card",
        ],
        "Salary": ["payroll", "salary", "pay cheque", "direct deposit", "deposit"],
        "Transfer": ["transfer", "interac", "e-transfer", "eft"],
        "Entertainment": [
            "netflix",
            "spotify",
            "movie",
            "cinema",
            "theatre",
            "concert",
        ],
        "Healthcare": [
            "pharmacy",
            "drug",
            "hospital",
            "clinic",
            "doctor",
            "dentist",
        ],
        "Subscription": ["subscription", "membership", "monthly fee"],
        "Insurance": ["insurance"],
        "ATM/Cash": ["atm", "cash"],
        "Interest/Fees": ["interest", "fee", "service charge"],
        "Fitness": [
            "gym",
            "fitness",
            "evolve strength post",
            "evolve strength",
            "evolve",
        ],
        "Avoidable Expenses": [
            "vapezilla smoke shop",
            "the blarney stone",
            "the portside pub",
            "viti wine and lager",
        ],
    }

    def __init__(
        self,
        merchant_memory: Optional[MerchantMemory] = None,
        category_rules: Optional[Dict[str, List[str]]] = None,
        fuzzy_threshold: int = FUZZY_MATCH_THRESHOLD,
    ):
        """
        Initialize the categorizer.

        Args:
            merchant_memory: MerchantMemory instance (creates new if None).
            category_rules: Custom category rules dict (uses defaults if None).
            fuzzy_threshold: Similarity threshold for fuzzy matching (0-100).
        """
        self.merchant_memory = merchant_memory or MerchantMemory()
        self.category_rules = category_rules or self.DEFAULT_RULES
        self.fuzzy_threshold = fuzzy_threshold

        # Build a lookup of all known merchants from rules
        self._known_merchants = self._build_known_merchants()

    def _build_known_merchants(self) -> Dict[str, str]:
        """
        Build a mapping of keywords to categories from rules.

        Returns:
            Dictionary mapping keywords to categories.
        """
        mapping = {}
        for category, keywords in self.category_rules.items():
            for keyword in keywords:
                mapping[keyword] = category
        return mapping

    def categorize(
        self,
        description: str,
        learn: bool = False,
    ) -> Tuple[str, float]:
        """
        Categorize a transaction with confidence score.

        Uses three strategies in order:
        1. Exact merchant memory match (confidence: HIGH)
        2. Fuzzy matching on normalized merchants (confidence: MEDIUM)
        3. Keyword rules fallback (confidence: LOW)

        Args:
            description: Transaction description/merchant name.
            learn: If True, remembers the categorization for future use.

        Returns:
            Tuple of (category, confidence_score) where confidence is 0.0-1.0.
        """
        if not description or not isinstance(description, str):
            return DEFAULT_CATEGORY, 0.0

        normalized_desc = normalize_description(description)
        merchant = normalize_merchant_name(description)

        # Strategy 1: Exact merchant memory match
        category = self.merchant_memory.get(merchant)
        if category:
            logger.debug(
                f"Memory match: '{merchant}' -> {category} (confidence: {CATEGORY_CONFIDENCE_HIGH})"
            )
            return category, CATEGORY_CONFIDENCE_HIGH

        # Strategy 2: Fuzzy matching on merchants
        category, confidence = self._fuzzy_match(merchant)
        if category and confidence > 0.0:
            logger.debug(
                f"Fuzzy match: '{merchant}' -> {category} (confidence: {confidence})"
            )
            if learn:
                self.merchant_memory.learn(merchant, category)
            return category, confidence

        # Strategy 3: Keyword rules
        category = self._keyword_match(normalized_desc)
        if category != DEFAULT_CATEGORY:
            logger.debug(
                f"Keyword match: '{description}' -> {category} (confidence: {CATEGORY_CONFIDENCE_LOW})"
            )
            if learn:
                self.merchant_memory.learn(merchant, category)
            return category, CATEGORY_CONFIDENCE_LOW

        logger.debug(f"No match found for '{description}'")
        return DEFAULT_CATEGORY, 0.0

    def _fuzzy_match(self, merchant: str) -> Tuple[str, float]:
        """
        Find best fuzzy match for a merchant among known merchants.

        Args:
            merchant: Normalized merchant name.

        Returns:
            Tuple of (best_matching_category, confidence) or (DEFAULT_CATEGORY, 0.0).
        """
        best_match = None
        best_score = 0

        for known_merchant, category in self._known_merchants.items():
            score = fuzz.token_set_ratio(merchant, known_merchant) / 100.0
            if score > best_score:
                best_score = score
                best_match = (category, score)

        if best_match and best_score * 100 >= self.fuzzy_threshold:
            return best_match[0], best_match[1]

        return DEFAULT_CATEGORY, 0.0

    def _keyword_match(self, normalized_description: str) -> str:
        """
        Match transaction to category using keyword rules.

        Args:
            normalized_description: Normalized (lowercase, no special chars) description.

        Returns:
            Matched category or DEFAULT_CATEGORY.
        """
        for category, keywords in self.category_rules.items():
            for keyword in keywords:
                if keyword in normalized_description:
                    return category

        return DEFAULT_CATEGORY

    def learn(self, merchant: str, category: str) -> None:
        """
        Teach the categorizer about a merchant.

        Args:
            merchant: Merchant name.
            category: Correct category for this merchant.
        """
        self.merchant_memory.learn(merchant, category)

    def update_rules(self, category_rules: Dict[str, List[str]]) -> None:
        """
        Update or replace category rules.

        Args:
            category_rules: New category rules dictionary.
        """
        self.category_rules = category_rules
        self._known_merchants = self._build_known_merchants()
        logger.info("Category rules updated")

    def add_category_rule(self, category: str, keywords: List[str]) -> None:
        """
        Add keywords to an existing category.

        Args:
            category: Category name.
            keywords: List of keywords to associate with category.
        """
        if category not in self.category_rules:
            self.category_rules[category] = []

        for keyword in keywords:
            if keyword not in self.category_rules[category]:
                self.category_rules[category].append(keyword)

        self._known_merchants = self._build_known_merchants()
        logger.debug(f"Added {len(keywords)} keywords to '{category}'")
