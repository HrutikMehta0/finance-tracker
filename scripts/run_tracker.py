#!/usr/bin/env python
"""
CLI tool to parse RBC CSV transaction files and display categorized transactions.

Usage:
    python scripts/run_tracker.py test_statement.csv --account chequing
"""
import argparse
import sys
from pathlib import Path

# Add the parent directory to sys.path so we can import finance_tracker
sys.path.insert(0, str(Path(__file__).parent.parent))

from finance_tracker.parser import parse_rbc_csv, transactions_from_df, export_transactions_to_xlsx


def main():
    parser = argparse.ArgumentParser(
        description="Parse RBC CSV transaction files and categorize them."
    )
    parser.add_argument(
        "csv_file",
        type=str,
        help="Path to the RBC CSV file to parse.",
    )
    parser.add_argument(
        "--account",
        type=str,
        required=True,
        help="Account name (e.g., 'chequing', 'savings').",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="transactions.xlsx",
        help="Output Excel file path (default: transactions.xlsx).",
    )

    args = parser.parse_args()

    csv_path = args.csv_file
    account = args.account
    output_path = args.output

    # Check if file exists
    if not Path(csv_path).exists():
        print(f"Error: File '{csv_path}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        # Parse the CSV
        df = parse_rbc_csv(csv_path, account)

        # Convert to Transaction objects
        transactions = transactions_from_df(df)

        # Export to Excel
        export_transactions_to_xlsx(transactions, output_path)
        print(f"✓ Exported {len(transactions)} transactions to '{output_path}'")

    except Exception as e:
        print(f"Error parsing CSV: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
