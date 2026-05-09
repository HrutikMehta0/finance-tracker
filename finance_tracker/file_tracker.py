"""
Processed file tracking system.

Maintains a persistent record of which statement files have been successfully
processed to avoid reprocessing and duplicate transactions.

Structure of processed_files.json:
{
    "processed_files": {
        "absolute/path/to/Jan.csv": {
            "processed_at": "2024-01-15T10:30:00",
            "file_size": 12345,
            "file_hash": "abc123...",
            "row_count": 45,
            "account": "chequing",
            "transactions_added": 42
        }
    }
}
"""
import json
import logging
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Dict, Optional

from .constants import PROCESSED_FILES_PATH

logger = logging.getLogger(__name__)


class FileTracker:
    """
    Manages persistent tracking of processed statement files.

    Prevents reprocessing of files and tracks how many transactions
    were added from each file.
    """

    def __init__(self, tracker_file: str = PROCESSED_FILES_PATH):
        """
        Initialize file tracker.

        Args:
            tracker_file: Path to processed_files.json.
        """
        self.tracker_file = Path(tracker_file)
        self.tracker_dir = self.tracker_file.parent
        self.data: Dict = {"processed_files": {}}
        self._load_tracker()

    def _load_tracker(self) -> None:
        """Load processed files registry from JSON file."""
        try:
            if self.tracker_file.exists():
                with open(self.tracker_file, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                logger.debug(
                    f"Loaded {len(self.data.get('processed_files', {}))} processed files"
                )
            else:
                self.data = {"processed_files": {}}
                logger.debug("No processed files registry found, starting fresh")
        except Exception as e:
            logger.warning(f"Failed to load file tracker: {e}, starting fresh")
            self.data = {"processed_files": {}}

    def _save_tracker(self) -> None:
        """Save processed files registry to JSON file."""
        try:
            self.tracker_dir.mkdir(parents=True, exist_ok=True)
            with open(self.tracker_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved file tracker to {self.tracker_file}")
        except Exception as e:
            logger.error(f"Failed to save file tracker: {e}")
            raise

    def _compute_file_hash(self, file_path: Path) -> str:
        """
        Compute SHA256 hash of file contents.

        Args:
            file_path: Path to file.

        Returns:
            Hex digest of file hash.
        """
        sha = sha256()
        with open(file_path, "rb") as f:
            sha.update(f.read())
        return sha.hexdigest()

    def is_processed(self, file_path: str) -> bool:
        """
        Check if a file has already been processed.

        Args:
            file_path: Absolute path to statement file.

        Returns:
            True if file has been processed, False otherwise.
        """
        return str(file_path) in self.data["processed_files"]

    def mark_processed(
        self,
        file_path: str,
        account: str,
        row_count: int,
        transactions_added: int,
    ) -> None:
        """
        Mark a file as successfully processed.

        Args:
            file_path: Absolute path to statement file.
            account: Account name (e.g., 'chequing', 'savings').
            row_count: Total rows in the file.
            transactions_added: Number of transactions added to workbook.
        """
        path = Path(file_path)
        file_key = str(path.resolve())

        self.data["processed_files"][file_key] = {
            "processed_at": datetime.now().isoformat(),
            "file_size": path.stat().st_size if path.exists() else 0,
            "file_hash": self._compute_file_hash(path) if path.exists() else "",
            "row_count": row_count,
            "account": account,
            "transactions_added": transactions_added,
        }

        self._save_tracker()
        logger.info(
            f"Marked {path.name} as processed "
            f"({transactions_added} transactions added)"
        )

    def get_processed_file_info(self, file_path: str) -> Optional[Dict]:
        """
        Get information about a processed file.

        Args:
            file_path: Absolute path to statement file.

        Returns:
            Dictionary with processing information or None if not processed.
        """
        return self.data["processed_files"].get(str(file_path))

    def get_all_processed(self) -> Dict[str, Dict]:
        """
        Get all processed files and their information.

        Returns:
            Dictionary mapping file paths to processing information.
        """
        return self.data["processed_files"].copy()

    def unmark_processed(self, file_path: str) -> None:
        """
        Remove a file from the processed files list.

        Useful for reprocessing a file (e.g., if there were errors).

        Args:
            file_path: Absolute path to statement file.
        """
        file_key = str(file_path)
        if file_key in self.data["processed_files"]:
            del self.data["processed_files"][file_key]
            self._save_tracker()
            logger.info(f"Unmarked {Path(file_path).name} as processed")

    def clear_all(self) -> None:
        """Clear all processed files. Use with caution!"""
        self.data = {"processed_files": {}}
        self._save_tracker()
        logger.warning("Cleared all processed file records")

    def get_summary(self) -> Dict:
        """
        Get summary statistics about processed files.

        Returns:
            Dictionary with statistics.
        """
        processed = self.data["processed_files"]
        total_files = len(processed)
        total_transactions = sum(f.get("transactions_added", 0) for f in processed.values())
        total_rows = sum(f.get("row_count", 0) for f in processed.values())

        return {
            "total_processed_files": total_files,
            "total_rows_processed": total_rows,
            "total_transactions_added": total_transactions,
        }
