# Architecture & Design Decisions

## Overview

Finance Tracker uses a modular, layered architecture designed for scalability, maintainability, and extensibility.

## Layer Architecture

```
┌─────────────────────────────────────┐
│     Scripts/CLI (run_tracker.py)    │
│     User-facing Interface Layer     │
└──────────────┬──────────────────────┘
               │
┌──────────────┴──────────────────────┐
│     Application Layer               │
│  ┌──────────────────────────────────┤
│  │ • Categorizer                    │
│  │ • Exporter                       │
│  │ • ConfigLoader                   │
│  │ • SummaryGenerator (TODO)        │
│  └──────────────────────────────────┤
└──────────────┬──────────────────────┘
               │
┌──────────────┴──────────────────────┐
│     Domain Layer                    │
│  ┌──────────────────────────────────┤
│  │ • Parser                         │
│  │ • Normalizer                     │
│  │ • Deduplicator                   │
│  │ • MerchantMemory                 │
│  └──────────────────────────────────┤
└──────────────┬──────────────────────┘
               │
┌──────────────┴──────────────────────┐
│     Data Layer                      │
│  ┌──────────────────────────────────┤
│  │ • Models (Transaction)           │
│  │ • Constants                      │
│  │ • merchant_memory.json           │
│  └──────────────────────────────────┤
└────────────────────────────────────┘
```

## Key Design Decisions

### 1. Separation of Concerns

Each module has a single, well-defined responsibility:

- **parser.py**: Handles CSV structure detection and data extraction only
- **categorizer.py**: Implements intelligent categorization logic
- **normalizer.py**: Text normalization and standardization
- **deduplicator.py**: Transaction identification and duplicate detection
- **merchant_memory.py**: Persistent merchant-to-category mappings
- **exporter.py**: Format-specific output generation

**Rationale**: Easier to test, modify, and extend individual components without affecting others.

### 2. Categorizer Multi-Strategy Approach

The `Categorizer` class uses a priority-ordered matching strategy:

```
Input Transaction
        │
        ├─→ Exact Merchant Memory Match?
        │        │
        │        └─→ YES: Return (category, HIGH_CONFIDENCE)
        │
        ├─→ Fuzzy Match Known Merchants?
        │        │
        │        └─→ YES: Return (category, MEDIUM_CONFIDENCE)
        │
        └─→ Keyword Rule Match?
                 │
                 └─→ YES: Return (category, LOW_CONFIDENCE)
                 └─→ NO: Return (UNCATEGORIZED, 0.0)
```

**Rationale**:
- Merchant memory provides fast, high-confidence matches for learned merchants
- Fuzzy matching handles typos without slowing down common cases
- Keyword rules provide a reasonable fallback
- Confidence scores allow downstream processing to handle uncertain matches

### 3. Dependency Injection

Components accept dependencies via constructor:

```python
# Good
categorizer = Categorizer(merchant_memory=my_memory)
exporter = Exporter()

# Not in this codebase (avoid)
# categorizer = Categorizer()  # Creates its own memory
```

**Rationale**: 
- Easier to test (inject mocks)
- More flexible (different memory implementations)
- Clearer dependencies between components

### 4. Immutable Data Processing

Functions return new objects rather than modifying inputs:

```python
# Good
df_clean = remove_duplicate_transactions(df)

# Not in this codebase (avoid)
# remove_duplicate_transactions(df)  # Modifies df in-place
```

**Rationale**: Prevents unexpected side effects and makes code easier to reason about.

### 5. Type Hints Throughout

All public functions have complete type hints:

```python
def categorize(
    self,
    description: str,
    learn: bool = False,
) -> Tuple[str, float]:
    """Categorize with confidence score."""
```

**Rationale**: 
- Better IDE support (autocomplete, type checking)
- Self-documenting code
- Enables static type checking with mypy

### 6. Persistent Merchant Learning

Learned merchants are stored in `data/merchant_memory.json`:

```json
{
  "Tim Hortons": "Dining",
  "Uber": "Transport"
}
```

**Rationale**:
- Improves categorization over time
- Survives application restarts
- Human-readable for manual review/editing
- Simple JSON format (no database dependency)

### 7. Logging Over Print Statements

All output uses Python's `logging` module:

```python
logger.info(f"Parsed {len(df)} transactions")
logger.debug(f"Category: {category} (confidence: {confidence})")
logger.warning(f"Merchant memory not found: {memory_file}")
```

**Rationale**:
- Consistent output format
- Different log levels for different verbosity needs
- Easy to redirect to files or logging services
- Supported by production deployments

## Performance Considerations

### Caching

The `Categorizer` builds a keyword lookup dictionary once during initialization:

```python
self._known_merchants = self._build_known_merchants()  # O(n) once
# Later: O(1) lookups
```

### Database Normalization

Column names are normalized once when reading CSV:

```python
df.columns = [normalize_column_name(col) for col in df.columns]
```

### Vectorized Operations

Heavy lifting uses pandas vectorized operations:

```python
df["amount"] = pd.to_numeric(...)  # Faster than row-by-row
df["dates"] = pd.to_datetime(...)
```

## Extensibility Points

### Adding New Categories

Option 1: Add keywords at runtime:

```python
categorizer.add_category_rule("Pet Store", ["petco", "petsmart"])
```

Option 2: Modify the default rules in `constants.py` and rebuild.

### Supporting New File Formats

Add a new parser function:

```python
# In parser.py
def parse_td_csv(file_path: str, account: str) -> pd.DataFrame:
    """Parse TD Bank CSV format."""
    # Implementation
```

Or add PDF support:

```python
# In parser.py  
def parse_rbc_pdf(file_path: str, account: str) -> pd.DataFrame:
    """Extract transactions from RBC PDF statement."""
    # Implementation
```

### Custom Export Formats

Extend the `Exporter` class:

```python
@staticmethod
def to_custom_format(transactions: List[Transaction], path: str) -> None:
    """Export in custom format."""
    # Implementation
```

### Google Sheets Integration

The `sheets.py` stub is ready for implementation using `gspread`:

```python
# sheets.py (to be implemented)
class GoogleSheetsManager:
    def read_transactions(self, spreadsheet_id: str) -> List[Transaction]:
        # Fetch from Google Sheets
        
    def write_transactions(self, transactions: List[Transaction]):
        # Sync to Google Sheets
```

## Testing Strategy

Unit tests cover the boundary between layers:

1. **Test Normalizer**: Pure functions, easy to test in isolation
2. **Test Deduplicator**: Hash consistency, duplicate detection logic
3. **Test Categorizer**: Multi-strategy matching with mocked memory
4. **Test Parser**: DataFrame conversion, missing column handling

Integration tests would cover:
- End-to-end CSV parsing and categorization
- Merchant memory persistence
- Export to multiple formats

## Future Enhancements

### Short-term

1. **PDF Statement Parsing**: Extract transactions from PDF statements
2. **Multiple Bank Support**: Add parsers for TD, BMO, Scotia, etc.
3. **Budget Tracking**: Define spending limits per category

### Medium-term

1. **Google Sheets Sync**: Real-time transaction sync with Sheets
2. **Web UI**: Browser-based interface with Streamlit
3. **Database Backend**: SQLite for transaction history

### Long-term

1. **Machine Learning**: Learn categorization patterns from user behavior
2. **Mobile App**: Native mobile app for transaction management
3. **Financial Aggregation**: Connect to multiple bank APIs
4. **Predictive Analytics**: Forecast spending patterns

## Dependencies and Rationale

| Package | Usage | Rationale |
|---------|-------|-----------|
| pandas | Data processing | Industry standard, excellent CSV support |
| rapidfuzz | Fuzzy matching | Fast, accurate string similarity |
| openpyxl | Excel export | Low-level control over formatting |
| gspread | Google Sheets | Simple Google Sheets API wrapper |
| google-auth | Google API auth | Official authentication library |

## Code Quality Metrics

Target standards:

- **Type Coverage**: 100% (all public functions type-hinted)
- **Docstring Coverage**: 100% (all public functions and classes documented)
- **Test Coverage**: >80% (focus on business logic)
- **Cyclomatic Complexity**: <5 per function (keep functions simple)
- **Line Length**: <100 characters (readability)

## Error Handling Strategy

1. **Validation Layer** (parser.py): Check file exists, contains expected columns
2. **Transformation Layer** (normalizer, deduplicator): Handle None/empty values gracefully
3. **Application Layer** (categorizer, exporter): Return sensible defaults
4. **CLI Layer** (run_tracker.py): User-friendly error messages

---

**Last Updated**: May 2026
