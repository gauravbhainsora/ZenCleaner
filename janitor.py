"""
ZenCleaner - Installer & Disk Bloat Janitor
Finds heavy .dmg, .pkg, .iso installers hogging disk space.
Safely moves selected files to macOS Trash with full undo support.
"""

import os
import time
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from cleaner import human_size, JOURNAL_DIR

TRASH_JOURNAL_FILE = JOURNAL_DIR / "trash_history.json"
INSTALLER_EXTENSIONS = {".dmg", ".pkg", ".iso"}

class InstallerJanitor:
    def __init__(self, search_roots: Optional[List[Path]] = None):
        if search_roots is None:
            self.search_roots = [
                Path.home() / "Downloads" / "Organized" / "Installers",
                Path.home() / "Downloads",
                Path.home() / "Desktop" / "Organized" / "Installers",
                Path.home() / "Desktop"
            ]
        else:
            self.search_roots = search_roots

        JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
        if not TRASH_JOURNAL_FILE.exists():
            TRASH_JOURNAL_FILE.write_text(json.dumps({"sessions": []}, indent=2))

    def scan(self, age_threshold_days: int = 14) -> Dict[str, Any]:
        """Scans for installers and categorizes by age."""
        found_files = []
        seen_paths = set()
        now = time.time()

        for root in self.search_roots:
            if not root.exists():
                continue
            
            # If scanning a general folder (like Downloads root), don't recurse deeply;
            # but if scanning an Installers folder, check all items.
            is_installers_folder = root.name.lower() == "installers"
            iterator = root.iterdir() if not is_installers_folder else root.rglob("*")

            for item in iterator:
                if item.is_dir() or item.suffix.lower() not in INSTALLER_EXTENSIONS:
                    continue

                abs_path = str(item.resolve())
                if abs_path in seen_paths:
                    continue
                seen_paths.add(abs_path)

                try:
                    stat = item.stat()
                    size_bytes = stat.st_size
                    mtime = stat.st_mtime
                    age_seconds = now - mtime
                    age_days = int(age_seconds / 86400)
                    is_old = age_days >= age_threshold_days
                    
                    if age_days == 0:
                        age_str = "Today"
                    elif age_days == 1:
                        age_str = "Yesterday"
                    elif age_days < 30:
                        age_str = f"{age_days} days ago"
                    else:
                        months = age_days // 30
                        age_str = f"{months} mo ago ({age_days}d)"

                    modified_date = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")

                    found_files.append({
                        "path": abs_path,
                        "filename": item.name,
                        "extension": item.suffix.lower(),
                        "size_bytes": size_bytes,
                        "size_str": human_size(size_bytes),
                        "age_days": age_days,
                        "age_str": age_str,
                        "modified_date": modified_date,
                        "is_old": is_old,
                        "recommended_trash": is_old
                    })
                except Exception:
                    continue

        # Sort by size descending (heaviest files first)
        found_files.sort(key=lambda x: x["size_bytes"], reverse=True)

        total_bytes = sum(f["size_bytes"] for f in found_files)
        old_bytes = sum(f["size_bytes"] for f in found_files if f["is_old"])

        return {
            "installers": found_files,
            "total_count": len(found_files),
            "total_size": human_size(total_bytes),
            "total_bytes": total_bytes,
            "reclaimable_count": sum(1 for f in found_files if f["is_old"]),
            "reclaimable_size": human_size(old_bytes),
            "reclaimable_bytes": old_bytes
        }

    def move_to_trash(self, file_paths: List[str]) -> Dict[str, Any]:
        """Safely moves specified files to macOS Trash (~/.Trash)."""
        trash_dir = Path.home() / ".Trash"
        trash_dir.mkdir(parents=True, exist_ok=True)

        session_id = datetime.now().strftime("trash_%Y%m%d_%H%M%S")
        journal_entries = []
        trashed_count = 0
        reclaimed_bytes = 0
        errors = []

        for p_str in file_paths:
            src = Path(p_str)
            if not src.exists():
                continue

            try:
                dest = trash_dir / src.name
                # Avoid collision inside Trash
                if dest.exists():
                    stem = src.stem
                    suffix = src.suffix
                    counter = 1
                    while (trash_dir / f"{stem} ({counter}){suffix}").exists():
                        counter += 1
                    dest = trash_dir / f"{stem} ({counter}){suffix}"

                file_size = src.stat().st_size
                shutil.move(str(src), str(dest))
                trashed_count += 1
                reclaimed_bytes += file_size

                journal_entries.append({
                    "original_path": str(src),
                    "trash_path": str(dest),
                    "size_bytes": file_size
                })
            except Exception as e:
                errors.append({"file": src.name, "error": str(e)})

        if journal_entries:
            self._record_trash_session(session_id, journal_entries)

        return {
            "session_id": session_id,
            "trashed_count": trashed_count,
            "reclaimed_size": human_size(reclaimed_bytes),
            "reclaimed_bytes": reclaimed_bytes,
            "errors": errors
        }

    def _record_trash_session(self, session_id: str, entries: List[Dict]):
        try:
            data = json.loads(TRASH_JOURNAL_FILE.read_text())
        except Exception:
            data = {"sessions": []}

        data["sessions"].append({
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "items": entries
        })
        TRASH_JOURNAL_FILE.write_text(json.dumps(data, indent=2))

    @staticmethod
    def undo_last_trash() -> Dict[str, Any]:
        """Restores files from ~/.Trash back to their original locations."""
        if not TRASH_JOURNAL_FILE.exists():
            return {"success": False, "message": "No trash history found."}

        try:
            data = json.loads(TRASH_JOURNAL_FILE.read_text())
        except Exception as e:
            return {"success": False, "message": f"Corrupted trash history: {e}"}

        sessions = data.get("sessions", [])
        if not sessions:
            return {"success": False, "message": "No trash sessions available to undo."}

        last_session = sessions.pop()
        restored = 0
        failed = 0

        for item in last_session["items"]:
            trash_path = Path(item["trash_path"])
            orig_path = Path(item["original_path"])

            if trash_path.exists():
                try:
                    orig_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(trash_path), str(orig_path))
                    restored += 1
                except Exception:
                    failed += 1
            else:
                failed += 1

        TRASH_JOURNAL_FILE.write_text(json.dumps(data, indent=2))

        return {
            "success": True,
            "session_id": last_session["session_id"],
            "restored_count": restored,
            "failed_count": failed
        }
