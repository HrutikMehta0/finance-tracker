"""
Application-wide constants and configuration defaults.
"""

# Categorization defaults
DEFAULT_CATEGORY = "Uncategorized"
FUZZY_MATCH_THRESHOLD = 80  # Similarity threshold (0-100)
CATEGORY_CONFIDENCE_HIGH = 0.95
CATEGORY_CONFIDENCE_MEDIUM = 0.75
CATEGORY_CONFIDENCE_LOW = 0.5

# File handling
SUPPORTED_CSV_EXTENSIONS = {".csv"}
SUPPORTED_EXCEL_EXTENSIONS = {".xlsx", ".xls"}
SUPPORTED_PDF_EXTENSIONS = {".pdf"}

# Merchant memory
MERCHANT_MEMORY_FILE = "data/merchant_memory.json"
MERCHANT_MEMORY_DIR = "data"

# Deduplication
HASH_ALGORITHM = "sha1"

# Transaction processing
DEFAULT_ACCOUNT = "unknown"

# Logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Workbook / data store (Excel is the source of truth)
DATA_DIR = "data"
TEMPLATES_DIR = "templates"
WORKBOOK_TEMPLATE_NAME = "finance_template.xlsx"

# Transaction sheet assumptions
TRANSACTION_SHEET_NAME = "Transactions"
TRANSACTION_SHEET_COLUMNS = [
	"Date",
	"Transaction Name",
	"Category",
	"Spent From",
	"Amount",
	"Notes",
	"Transaction ID",
]

# Processed files registry
PROCESSED_FILES_PATH = "data/processed_files.json"

# Logging file
LOG_DIR = "logs"
LOG_FILE = "logs/finance_tracker.log"

# Supported file extensions (combined)
SUPPORTED_EXTENSIONS = {".csv", ".pdf", ".xlsx", ".xls"}
