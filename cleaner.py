"""
ZenCleaner - Core Engine
Handles scanning, categorization, rule matching, safe moving, and rollback journal.
Zero third-party dependencies - standard library only!
"""

import os
import re
import sys
import json
import shutil
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any

JOURNAL_DIR = Path.home() / ".zencleaner"
JOURNAL_FILE = JOURNAL_DIR / "history.json"
CONFIG_FILE = JOURNAL_DIR / "config.json"

DEFAULT_RULES = [
    {
        "category": "Screenshots",
        "folder": "Screenshots",
        "subfolder_by_date": True,  # e.g. Screenshots/2026-05
        "name_patterns": [r"^Screenshot.*", r"^Screen Shot.*", r"^Screen Recording.*"],
        "extensions": [".png", ".jpg", ".jpeg", ".mov", ".mp4"]
    },
    {
        "category": "Receipts & Financial",
        "folder": "Documents/Receipts & Financial",
        "subfolder_by_date": False,
        "name_patterns": [
            r".*\b(receipt|invoice|bill|billing|statement|tax|taxes|paystub|payslip|salary|order_summary|uber|lyft)\b.*"
        ],
        "extensions": [".pdf", ".png", ".jpg", ".csv"]
    },
    {
        "category": "Documents & Reading",
        "folder": "Documents/PDFs & Books",
        "subfolder_by_date": False,
        "name_patterns": [],
        "extensions": [".pdf", ".epub", ".mobi", ".azw3"]
    },
    {
        "category": "Office & Spreadsheets",
        "folder": "Documents/Office",
        "subfolder_by_date": False,
        "name_patterns": [],
        "extensions": [".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt", ".key", ".numbers", ".pages", ".csv", ".tsv"]
    },
    {
        "category": "Installers & Disk Images",
        "folder": "Installers",
        "subfolder_by_date": False,
        "name_patterns": [],
        "extensions": [".dmg", ".pkg", ".iso", ".app"]
    },
    {
        "category": "Archives & Compressed",
        "folder": "Archives",
        "subfolder_by_date": False,
        "name_patterns": [],
        "extensions": [".zip", ".tar.gz", ".tgz", ".tar", ".gz", ".rar", ".7z", ".bz2", ".xz"]
    },
    {
        "category": "Audio & Music",
        "folder": "Audio",
        "subfolder_by_date": False,
        "name_patterns": [],
        "extensions": [".mp3", ".wav", ".aiff", ".flac", ".m4a", ".aac", ".ogg", ".alac"]
    },
    {
        "category": "Videos",
        "folder": "Videos",
        "subfolder_by_date": False,
        "name_patterns": [],
        "extensions": [".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"]
    },
    {
        "category": "Images & Graphics",
        "folder": "Images",
        "subfolder_by_date": False,
        "name_patterns": [],
        "extensions": [".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif", ".heic", ".ico", ".tiff", ".psd", ".ai"]
    },
    {
        "category": "Code & Development",
        "folder": "Developer",
        "subfolder_by_date": False,
        "name_patterns": [],
        "extensions": [".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".json", ".sql", ".sh", ".yaml", ".yml", ".rs", ".go", ".cpp", ".c", ".h"]
    },
    {
        "category": "Text & Notes",
        "folder": "Documents/Notes",
        "subfolder_by_date": False,
        "name_patterns": [],
        "extensions": [".txt", ".md", ".rtf", ".log"]
    }
]

IGNORE_NAMES = {
    ".ds_store", ".localized", "desktop.ini", "thumbs.db", ".git", ".gitignore",
    "organized", "$recycle.bin"
}

IGNORE_EXTENSIONS = {
    ".crdownload", ".download", ".part", ".tmp", ".swp"
}


def human_size(bytes_val: int) -> str:
    """Formats bytes to human-readable string (KB, MB, GB)."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} PB"


class ZenCleaner:
    def __init__(self, target_folder: Path, destination_root: Optional[Path] = None):
        self.target_folder = target_folder.resolve()
        # Default destination is inside the target folder under "Organized"
        self.destination_root = (destination_root or (self.target_folder / "Organized")).resolve()
        self.rules = self.load_rules()
        self._ensure_journal_dir()

    def _ensure_journal_dir(self):
        JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
        if not JOURNAL_FILE.exists():
            JOURNAL_FILE.write_text(json.dumps({"sessions": []}, indent=2))

    def load_rules(self) -> List[Dict]:
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f).get("rules", DEFAULT_RULES)
            except Exception:
                pass
        return DEFAULT_RULES

    def save_rules(self, rules: List[Dict]):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"rules": rules}, f, indent=2)
        self.rules = rules

    def classify_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Determines the target folder and category for a given file."""
        filename = file_path.name
        lower_name = filename.lower()
        suffix = file_path.suffix.lower()

        # Check ignore list
        if lower_name in IGNORE_NAMES or suffix in IGNORE_EXTENSIONS:
            return None
        if filename.startswith("."):
            return None

        # Check modified time (ignore if modified in the last 60 seconds - active downloads)
        try:
            mtime = file_path.stat().st_mtime
            if time.time() - mtime < 60:
                return None
        except Exception:
            return None

        for rule in self.rules:
            has_patterns = bool(rule.get("name_patterns"))
            pattern_match = False
            if has_patterns:
                for pattern in rule["name_patterns"]:
                    if re.match(pattern, filename, re.IGNORECASE):
                        pattern_match = True
                        break

            # Match extension
            ext_match = suffix in [ext.lower() for ext in rule.get("extensions", [])]

            # If rule has specific name patterns, it must match the pattern AND the extension
            # If rule has no name patterns, it only needs to match the extension
            matched = False
            if has_patterns:
                matched = pattern_match and (ext_match if rule.get("extensions") else True)
            else:
                matched = ext_match

            if matched:
                subfolder = rule["folder"]
                if rule.get("subfolder_by_date"):
                    dt = datetime.fromtimestamp(mtime)
                    subfolder = f"{subfolder}/{dt.strftime('%Y-%m')}"

                return {
                    "category": rule["category"],
                    "relative_folder": subfolder,
                    "target_dir": self.destination_root / subfolder
                }

        # Fallback category for unknown extensions
        return {
            "category": "Other Files",
            "relative_folder": "Other",
            "target_dir": self.destination_root / "Other"
        }

    def scan(self) -> List[Dict[str, Any]]:
        """Scans the target folder and returns proposed moves."""
        moves = []
        if not self.target_folder.exists():
            return moves

        for item in self.target_folder.iterdir():
            # Don't organize directories (only files directly in the root)
            if item.is_dir():
                continue
            
            # Skip if it is inside destination root
            if self.destination_root in item.parents or item == self.destination_root:
                continue

            classification = self.classify_file(item)
            if not classification:
                continue

            target_dir = classification["target_dir"]
            dest_file = self._resolve_collision(target_dir / item.name)

            try:
                stat = item.stat()
                file_size = stat.st_size
                mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            except Exception:
                file_size = 0
                mtime = "Unknown"

            moves.append({
                "source": str(item),
                "filename": item.name,
                "category": classification["category"],
                "relative_folder": classification["relative_folder"],
                "destination": str(dest_file),
                "size_bytes": file_size,
                "size_str": human_size(file_size),
                "modified": mtime
            })

        return moves

    def _resolve_collision(self, dest_path: Path) -> Path:
        """Appends (1), (2) if destination file already exists."""
        if not dest_path.exists():
            return dest_path
        
        base_stem = dest_path.stem
        suffix = dest_path.suffix
        counter = 1
        while dest_path.exists():
            dest_path = dest_path.parent / f"{base_stem} ({counter}){suffix}"
            counter += 1
        return dest_path

    def execute_plan(self, moves: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Executes the proposed file moves and logs to journal."""
        session_id = datetime.now().strftime("session_%Y%m%d_%H%M%S")
        journal_entries = []
        moved_count = 0
        total_bytes = 0
        errors = []

        for move in moves:
            src = Path(move["source"])
            dst = Path(move["destination"])

            if not src.exists():
                continue

            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))
                moved_count += 1
                total_bytes += move.get("size_bytes", 0)

                journal_entries.append({
                    "source": str(src),
                    "destination": str(dst),
                    "size_bytes": move.get("size_bytes", 0)
                })
            except Exception as e:
                errors.append({"file": src.name, "error": str(e)})

        # Record to history
        if journal_entries:
            self._record_session(session_id, journal_entries)

        return {
            "session_id": session_id,
            "moved_count": moved_count,
            "total_size": human_size(total_bytes),
            "errors": errors
        }

    def _record_session(self, session_id: str, entries: List[Dict]):
        try:
            data = json.loads(JOURNAL_FILE.read_text())
        except Exception:
            data = {"sessions": []}

        data["sessions"].append({
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "target_folder": str(self.target_folder),
            "moves": entries
        })
        JOURNAL_FILE.write_text(json.dumps(data, indent=2))

    @staticmethod
    def undo_last_session() -> Dict[str, Any]:
        """Restores files from the most recent session back to original paths."""
        if not JOURNAL_FILE.exists():
            return {"success": False, "message": "No cleanup history found."}

        try:
            data = json.loads(JOURNAL_FILE.read_text())
        except Exception as e:
            return {"success": False, "message": f"Corrupted history file: {e}"}

        sessions = data.get("sessions", [])
        if not sessions:
            return {"success": False, "message": "No sessions available to undo."}

        last_session = sessions.pop()
        restored = 0
        failed = 0

        for item in last_session["moves"]:
            cur_path = Path(item["destination"])
            orig_path = Path(item["source"])

            if cur_path.exists():
                try:
                    orig_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(cur_path), str(orig_path))
                    restored += 1
                except Exception:
                    failed += 1
            else:
                failed += 1

        # Clean up empty organized folders if left empty
        JOURNAL_FILE.write_text(json.dumps(data, indent=2))

        return {
            "success": True,
            "session_id": last_session["session_id"],
            "restored_count": restored,
            "failed_count": failed
        }

    @staticmethod
    def get_stats() -> Dict[str, Any]:
        """Returns historical statistics."""
        if not JOURNAL_FILE.exists():
            return {"total_sessions": 0, "total_files_organized": 0}

        try:
            data = json.loads(JOURNAL_FILE.read_text())
            sessions = data.get("sessions", [])
            total_moves = sum(len(s.get("moves", [])) for s in sessions)
            total_bytes = sum(sum(m.get("size_bytes", 0) for m in s.get("moves", [])) for s in sessions)
            return {
                "total_sessions": len(sessions),
                "total_files_organized": total_moves,
                "total_bytes_organized": human_size(total_bytes),
                "last_session": sessions[-1]["timestamp"] if sessions else None
            }
        except Exception:
            return {"total_sessions": 0, "total_files_organized": 0}
