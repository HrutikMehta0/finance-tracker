#!/usr/bin/env python
"""
CLI tool to parse and categorize bank transaction files.

Supports RBC CSV exports with automatic merchant normalization,
persistent merchant memory, and intelligent categorization.

Usage:
    python scripts/run_tracker.py statement.csv --account chequing
    python scripts/run_tracker.py statement.csv --account savings -o output.xlsx
"""
import argparse
import logging
import sys
from pathlib import Path

# Add the parent directory to sys.path so we can import finance_tracker
sys.path.insert(0, str(Path(__file__).parent.parent))

from finance_tracker import (
    configure_logging,
    get_logger,
    FileTracker,
)
from finance_tracker.categorizer import Categorizer
from finance_tracker.constants import (
    LOG_FORMAT,
    LOG_DATE_FORMAT,
    PROCESSED_FILES_PATH,
    SUPPORTED_EXTENSIONS,
    DEFAULT_ACCOUNT,
)
from finance_tracker.exporter import Exporter
from finance_tracker.merchant_memory import MerchantMemory
from finance_tracker.parser import parse_statement, transactions_from_df
from finance_tracker.deduplicator import remove_duplicate_transactions

configure_logging()
logger = get_logger(__name__)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Local-first ETL: scan statements, parse, categorize, dedupe, append to workbook",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--statements-dir",
        type=str,
        required=True,
        help="Directory containing statement files (CSV/PDF/Excel).",
    )

    parser.add_argument(
        "--account",
        type=str,
        default=DEFAULT_ACCOUNT,
        help="Account name or identifier (e.g., 'chequing', 'savings').",
    )

    parser.add_argument(
        "--workbook",
        type=str,
        required=True,
        help="Path to the Excel workbook (source of truth) to append transactions to.",
    )

    parser.add_argument(
        "--remove-duplicates",
        action="store_true",
        help="Remove duplicate transactions before export.",
    )

    parser.add_argument(
        "--fuzzy-threshold",
        type=int,
        default=80,
        help="Fuzzy match threshold for merchant names (0-100, default: 80).",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging output.",
    )

    parser.add_argument(
        "--learn",
        action="store_true",
        help="Learn merchant categorizations for future use.",
    )

    args = parser.parse_args()

    # Configure logging verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        statements_dir = Path(args.statements_dir)
        account = args.account
        workbook_path = Path(args.workbook)

        if not statements_dir.exists() or not statements_dir.is_dir():
            logger.error(f"Statements directory not found: {statements_dir}")
            sys.exit(1)

        if not workbook_path.exists():
            logger.info(f"Workbook not found, creating new workbook at: {workbook_path}")

        logger.info(f"Scanning statements in: {statements_dir}")

        tracker = FileTracker(PROCESSED_FILES_PATH)
        categorizer = Categorizer(fuzzy_threshold=args.fuzzy_threshold)
        merchant_memory = MerchantMemory()

        all_transactions = []
        processed_count = 0
        skipped_count = 0

        for file in sorted(statements_dir.iterdir()):
            if file.is_dir():
                continue
            if file.suffix.lower() not in SUPPORTED_EXTENSIONS:
                logger.debug(f"Skipping unsupported file extension: {file}")
                continue

            abs_path = str(file.resolve())
            if tracker.is_processed(abs_path):
                logger.info(f"Already processed, skipping: {file.name}")
                skipped_count += 1
                continue

            try:
                logger.info(f"Processing file: {file.name}")
                df = parse_statement(abs_path, account)
                logger.info(f"Parsed {len(df)} rows from {file.name}")

                if args.remove_duplicates:
                    df = remove_duplicate_transactions(df)

                # Categorize
                df["category"] = df["description"].apply(
                    lambda desc: categorizer.categorize(desc, learn=args.learn)[0]
                )

                # Convert to Transaction objects and append
                txns = transactions_from_df(df)
                if txns:
                    Exporter.to_excel(txns, str(workbook_path))
                    tracker.mark_processed(
                        abs_path,
                        account=account,
                        row_count=len(df),
                        transactions_added=len(txns),
                    )
                    processed_count += 1
                    all_transactions.extend(txns)
                else:
                    logger.info(f"No transactions extracted from {file.name}; marking skipped")
                    tracker.mark_processed(abs_path, account=account, row_count=0, transactions_added=0)
                    skipped_count += 1

            except Exception as e:
                logger.error(f"Failed processing {file.name}: {e}")
                continue

        logger.info(f"ETL complete. Files processed: {processed_count}, skipped: {skipped_count}")
        print(f"\n✓ Files processed: {processed_count}, skipped: {skipped_count}")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=args.verbose)
        sys.exit(1)


if __name__ == "__main__":
    main()
