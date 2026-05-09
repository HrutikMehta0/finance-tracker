# Finance Tracker - Scalable Transaction Parser & Categorizer

A modular, production-quality Python library for parsing bank transaction CSVs, intelligently categorizing transactions, and exporting results.

## Features

- **Intelligent Categorization**: Multi-strategy approach using merchant memory, fuzzy matching, and keyword rules
- **Persistent Merchant Learning**: Learn and remember merchant categorizations in JSON
- **Fuzzy Matching**: Handle typos and variations in merchant names with `rapidfuzz`
- **Duplicate Detection**: Identify and remove duplicate transactions
- **Flexible Normalization**: Normalize merchant names and descriptions for consistency
- **Multiple Export Formats**: Export to Excel (.xlsx) or CSV
- **Logging**: Comprehensive logging throughout the application
- **Modular Architecture**: Clean separation of concerns with independent modules
- **Type Hints**: Full type annotations for better IDE support and type checking
- **Comprehensive Tests**: Unit tests for core functionality

## Architecture

### Module Overview

```
finance_tracker/
├── __init__.py              # Package exports and public API
├── models.py                # Core data classes (Transaction)
├── constants.py             # Application configuration constants
├── normalizer.py            # Text normalization utilities
├── deduplicator.py          # Transaction hashing and duplicate detection
├── categorizer.py           # Intelligent transaction categorization engine
├── merchant_memory.py       # Persistent merchant-to-category mappings
├── parser.py                # CSV file parsing and normalization
├── exporter.py              # Export to Excel/CSV
├── config_loader.py         # Configuration file management
├── summaries.py             # TODO: Summary and reporting (stub)
└── sheets.py                # TODO: Google Sheets integration (stub)
```

### Design Principles

1. **Single Responsibility**: Each module has one clear purpose
2. **Dependency Injection**: Components accept dependencies (e.g., MerchantMemory) rather than creating them
3. **Immutability**: Functions don't modify inputs; they return new values
4. **Type Safety**: Full type hints throughout
5. **Logging**: Consistent logging instead of print statements
6. **Testability**: Pure functions and dependency injection make testing easy
7. **Extensibility**: Easy to add new categories, rules, or export formats

### Categorization Strategy

The `Categorizer` class uses a three-tier matching strategy:

1. **Exact Memory Match** (Confidence: 0.95)
   - Checks persistent merchant memory for previously learned categorizations
   - Fastest match, most reliable

2. **Fuzzy Matching** (Confidence: 0.75)
   - Uses `rapidfuzz` to find similar merchants in the keyword rules
   - Configurable threshold (default: 80%)
   - Handles typos and variations

3. **Keyword Rules Fallback** (Confidence: 0.50)
   - Matches against a dictionary of category keywords
   - Includes pre-configured rules for common merchants
   - Can be customized or extended

## Installation

```bash
pip install -r requirements.txt
```

### Key Dependencies

- **pandas**: Data manipulation and CSV handling
- **rapidfuzz**: Fuzzy string matching for merchant names
- **openpyxl**: Excel file creation and manipulation
- **gspread**: Google Sheets integration (future)
- **google-auth**: Google API authentication (future)

## Usage

### Command-Line Interface

```bash
# Basic usage
python scripts/run_tracker.py statement.csv --account chequing

# With custom output file
python scripts/run_tracker.py statement.csv --account savings -o output.xlsx

# Remove duplicates
python scripts/run_tracker.py statement.csv --account chequing --remove-duplicates

# Learn merchant categorizations for future use
python scripts/run_tracker.py statement.csv --account chequing --learn

# Custom fuzzy threshold
python scripts/run_tracker.py statement.csv --account chequing --fuzzy-threshold 85

# Verbose logging
python scripts/run_tracker.py statement.csv --account chequing -v
```

### Python API

```python
from finance_tracker import Categorizer, parse_rbc_csv, Exporter, MerchantMemory

# Parse CSV file
df = parse_rbc_csv("statement.csv", account="chequing")

# Create categorizer with merchant memory
memory = MerchantMemory()
categorizer = Categorizer(merchant_memory=memory)

# Categorize transactions
for _, row in df.iterrows():
    category, confidence = categorizer.categorize(row['description'])
    print(f"{row['description']} -> {category} ({confidence:.0%})")

# Export results
from finance_tracker import transactions_from_df
transactions = transactions_from_df(df)
Exporter.to_excel(transactions, "output.xlsx")
```

### Normalization

```python
from finance_tracker import (
    normalize_merchant_name,
    normalize_description,
    normalize_column_name,
)

# Normalize merchant names
normalize_merchant_name("TIM HORTONS #4432")  # -> "Tim Hortons"
normalize_merchant_name("walmart  supercentre")  # -> "Walmart Supercentre"

# Normalize descriptions for categorization
normalize_description("STARBUCKS COFFEE #123")  # -> "starbucks coffee 123"

# Normalize column names
normalize_column_name("Transaction Date")  # -> "transaction_date"
normalize_column_name("Amount (CAD$)")  # -> "amount_cad"
```

### Deduplication

```python
from finance_tracker import (
    generate_transaction_hash,
    find_duplicate_transactions,
    remove_duplicate_transactions,
)

# Generate transaction hash
hash_id = generate_transaction_hash(
    date=datetime(2024, 1, 15),
    description="STARBUCKS COFFEE",
    amount=5.50,
    account="chequing"
)

# Find duplicates in DataFrame
duplicates = find_duplicate_transactions(df)

# Remove duplicates (keep first occurrence)
df_clean = remove_duplicate_transactions(df, keep="first")
```

### Merchant Memory

```python
from finance_tracker import MerchantMemory, Categorizer

# Create and use merchant memory
memory = MerchantMemory()

# Learn merchants
memory.learn("STARBUCKS", "Dining")
memory.learn("UBER", "Transport")

# Retrieve learned categories
category = memory.get("STARBUCKS")  # -> "Dining"

# Check if merchant is remembered
if memory.has_merchant("STARBUCKS"):
    print("Starbucks categorization known")

# Use with categorizer
categorizer = Categorizer(merchant_memory=memory)
category, confidence = categorizer.categorize("STARBUCKS #123")
# -> ("Dining", 0.95)  # High confidence from merchant memory
```

### Configuring Categorization Rules

```python
from finance_tracker import Categorizer

# Create categorizer with default rules
categorizer = Categorizer()

# Add new category with keywords
categorizer.add_category_rule("Pet Store", ["petco", "petsmart", "vca"])

# Or completely replace rules
custom_rules = {
    "Groceries": ["costco", "walmart", "supermarket"],
    "Coffee": ["starbucks", "second cup"],
}
categorizer.update_rules(custom_rules)
```

## Data Files

### Merchant Memory

Learned merchant categorizations are stored in `data/merchant_memory.json`:

```json
{
  "Tim Hortons": "Dining",
  "Starbucks": "Dining",
  "Uber": "Transport",
  "Rogers Internet": "Utilities"
}
```

This file is automatically created and updated when you use the `--learn` flag or call `categorizer.learn()`.

## Testing

Run the unit tests:

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_categorizer.py -v

# Run with coverage
python -m pytest tests/ --cov=finance_tracker
```

### Test Coverage

- **test_normalizer.py**: Text normalization functions
- **test_deduplicator.py**: Transaction hashing and duplicate detection
- **test_categorizer.py**: Categorization engine and merchant memory
- **test_parser.py**: CSV parsing and data transformation

## Configuration

Configuration can be loaded from a JSON file:

```python
from finance_tracker import ConfigLoader

config = ConfigLoader("config.json")

# Get configuration values
threshold = config.get("categorizer.fuzzy_threshold", 80)
output_dir = config.get("export.output_dir", "output")

# Or use class methods
from finance_tracker.config_loader import create_default_config
defaults = create_default_config()
```

## Future Enhancements

### TODO: Google Sheets Integration (`sheets.py`)

- Authenticate with Google API
- Read transactions from shared spreadsheets
- Write categorized transactions back to sheets
- Real-time sync capabilities
- Collaboration features

### TODO: Summary Generation (`summaries.py`)

- Category spending totals and distribution
- Monthly spending trends
- Merchant spending analysis
- Budget vs actual comparison
- Period-over-period comparisons
- Top merchants and categories

### TODO: PDF Banking Statement Support

- Parse PDF statements (using `pdfplumber`)
- Multiple bank format support
- Intelligent table detection and extraction

## Logging

The application uses Python's `logging` module. Configure logging as needed:

```python
import logging

# Set log level
logging.getLogger("finance_tracker").setLevel(logging.DEBUG)

# Or in your main script
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

## Error Handling

All public functions include proper error handling:

```python
from finance_tracker import parse_rbc_csv

try:
    df = parse_rbc_csv("statement.csv", account="chequing")
except FileNotFoundError:
    print("CSV file not found")
except ValueError as e:
    print(f"Cannot parse CSV: {e}")
```

## Performance Considerations

1. **Merchant Memory**: Uses in-memory dictionary for O(1) lookups; persisted to JSON
2. **Fuzzy Matching**: May be slow for large datasets; consider pre-learning common merchants
3. **DataFrame Operations**: Leverages pandas for efficient bulk processing
4. **Deduplication**: Uses transaction hash for fast duplicate detection

## Contributing

When adding new features:

1. Create separate modules for distinct concerns
2. Add full type hints
3. Include comprehensive docstrings
4. Write unit tests
5. Update this README

## License

[Add your license here]

## Support

For issues, questions, or feature requests, please [add contact/issue link here].

---

**Version**: 2.0.0  
**Last Updated**: May 2026
