#!/usr/bin/env python3
"""
ZenCleaner - Zero-Effort Desktop & Downloads Organizer for macOS
"""

import sys
import argparse
from cli import cmd_scan, cmd_clean, cmd_undo, cmd_stats, cmd_janitor
from web_server import run_web_dashboard

def main():
    parser = argparse.ArgumentParser(
        description="ZenCleaner - Zero-Effort Desktop & Downloads Organizer for macOS",
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Scan command (default)
    p_scan = subparsers.add_parser("scan", help="Preview loose files and planned organization (Dry Run)")
    p_scan.add_argument("target", nargs="?", default="desktop", help="Folder to scan: 'desktop', 'downloads', or custom path")

    # Clean command
    p_clean = subparsers.add_parser("clean", help="Organize files into clean categorized subfolders")
    p_clean.add_argument("target", nargs="?", default="desktop", help="Folder to clean: 'desktop', 'downloads', or custom path")
    p_clean.add_argument("--apply", "-y", action="store_true", help="Execute without asking for interactive confirmation")

    # Undo command
    subparsers.add_parser("undo", help="Undo the most recent cleanup session (restores all files back)")

    # Stats command
    subparsers.add_parser("stats", help="Display lifetime cleanup statistics")

    # Janitor command (Reclaim disk space)
    p_jan = subparsers.add_parser("janitor", aliases=["reclaim"], help="Find and safely trash old heavy installers (.dmg, .pkg)")
    p_jan.add_argument("--days", "-d", type=int, default=14, help="Age threshold in days (default: 14)")
    p_jan.add_argument("--apply", "-y", action="store_true", help="Move old installers to Trash without prompt")
    p_jan.add_argument("--undo", action="store_true", help="Restore recently trashed installers back from Trash")

    # UI / Dashboard command
    p_ui = subparsers.add_parser("ui", help="Launch interactive browser dashboard")
    p_ui.add_argument("--port", "-p", type=int, default=5050, help="Port to run dashboard server on (default: 5050)")

    args = parser.parse_args()

    if args.command == "clean":
        cmd_clean(args)
    elif args.command == "undo":
        cmd_undo(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif args.command in ["janitor", "reclaim"]:
        cmd_janitor(args)
    elif args.command == "ui":
        run_web_dashboard(args.port)
    else:
        # Default action is scan desktop if no args provided
        if not args.command:
            args.target = "desktop"
        cmd_scan(args)

if __name__ == "__main__":
    main()
