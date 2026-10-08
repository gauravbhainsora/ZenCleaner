"""
ZenCleaner - Command Line Interface
Provides rich, interactive terminal output with dry-run previews, safety confirmations, and undo.
"""

import sys
import argparse
from pathlib import Path
from collections import defaultdict
from cleaner import ZenCleaner, human_size

# ANSI color codes
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
RED = "\033[31m"
DIM = "\033[2m"

def resolve_target(target_arg: str) -> Path:
    target_arg = target_arg.lower().strip()
    if target_arg in ["desktop", "d"]:
        return Path.home() / "Desktop"
    elif target_arg in ["downloads", "dl"]:
        return Path.home() / "Downloads"
    else:
        p = Path(target_arg).expanduser().resolve()
        if not p.exists():
            print(f"{RED}Error: Folder '{target_arg}' does not exist!{RESET}")
            sys.exit(1)
        return p

def print_banner():
    print(f"""
{CYAN}{BOLD}╔══════════════════════════════════════════════════════════╗
║               🧹 ZenCleaner for macOS                    ║
║         Zero-Effort Desktop & Downloads Organizer        ║
╚══════════════════════════════════════════════════════════╝{RESET}
""")

def run_scan(cleaner: ZenCleaner) -> list:
    print(f"{BOLD}📂 Scanning target folder:{RESET} {CYAN}{cleaner.target_folder}{RESET}")
    moves = cleaner.scan()

    if not moves:
        print(f"\n{GREEN}✨ Everything is already clean! No loose files found to organize.{RESET}\n")
        return []

    # Group by category
    categories = defaultdict(list)
    total_bytes = 0
    for m in moves:
        categories[m["category"]].append(m)
        total_bytes += m["size_bytes"]

    print(f"\n{BOLD}Found {YELLOW}{len(moves)} loose files{RESET}{BOLD} ({human_size(total_bytes)}) ready to organize:{RESET}\n")

    for cat, items in sorted(categories.items()):
        cat_bytes = sum(i["size_bytes"] for i in items)
        print(f"  {MAGENTA}{BOLD}▶ {cat}{RESET} ({len(items)} files, {human_size(cat_bytes)}):")
        for item in items[:5]:  # preview up to 5 items per category
            dest_rel = Path(item["destination"]).relative_to(cleaner.destination_root)
            print(f"     {DIM}•{RESET} {item['filename']} {DIM}→ Organized/{dest_rel}{RESET}")
        if len(items) > 5:
            print(f"     {DIM}... and {len(items) - 5} more files{RESET}")
        print()

    print(f"{DIM}Target destination: {cleaner.destination_root}{RESET}\n")
    return moves

def cmd_scan(args):
    print_banner()
    target = resolve_target(args.target)
    cleaner = ZenCleaner(target)
    run_scan(cleaner)

def cmd_clean(args):
    print_banner()
    target = resolve_target(args.target)
    cleaner = ZenCleaner(target)
    moves = run_scan(cleaner)

    if not moves:
        return

    if not args.apply:
        print(f"{YELLOW}{BOLD}⚠️  This was a DRY RUN preview. No files were moved.{RESET}")
        choice = input(f"{BOLD}Would you like to organize these {len(moves)} files now? [y/N]: {RESET}").strip().lower()
        if choice not in ['y', 'yes']:
            print(f"{DIM}Operation cancelled. Files remain unchanged.{RESET}")
            return

    print(f"\n{CYAN}⚡ Organizing files...{RESET}")
    result = cleaner.execute_plan(moves)
    print(f"{GREEN}{BOLD}✅ Success!{RESET} Moved {BOLD}{result['moved_count']}{RESET} files ({result['total_size']}).")
    print(f"{DIM}Session ID: {result['session_id']} (Use 'python3 main.py undo' anytime to revert){RESET}\n")

def cmd_undo(args):
    print_banner()
    print(f"{CYAN}🔄 Reverting most recent cleanup session...{RESET}")
    result = ZenCleaner.undo_last_session()
    if result["success"]:
        print(f"{GREEN}{BOLD}✅ Undo completed!{RESET}")
        print(f"Restored {BOLD}{result['restored_count']}{RESET} files to their original locations.")
        if result["failed_count"] > 0:
            print(f"{YELLOW}Warning: {result['failed_count']} files could not be moved back (may have been renamed or deleted).{RESET}")
    else:
        print(f"{RED}❌ {result['message']}{RESET}")
    print()

def cmd_stats(args):
    print_banner()
    stats = ZenCleaner.get_stats()
    print(f"{BOLD}📊 ZenCleaner Lifetime Stats:{RESET}")
    print(f"  • Total cleanup sessions: {CYAN}{stats['total_sessions']}{RESET}")
    print(f"  • Total files organized:  {GREEN}{stats['total_files_organized']}{RESET}")
    print(f"  • Total data tidied:      {YELLOW}{stats.get('total_bytes_organized', '0 B')}{RESET}")
    if stats.get("last_session"):
        print(f"  • Last cleaned at:        {DIM}{stats['last_session']}{RESET}")
    print()

def cmd_janitor(args):
    print_banner()
    from janitor import InstallerJanitor
    janitor = InstallerJanitor()

    if getattr(args, "undo", False):
        print(f"{CYAN}🔄 Reverting most recent Trash session...{RESET}")
        res = janitor.undo_last_trash()
        if res["success"]:
            print(f"{GREEN}{BOLD}✅ Restored {res['restored_count']} files from Trash back to their original locations!{RESET}\n")
        else:
            print(f"{RED}❌ {res['message']}{RESET}\n")
        return

    data = janitor.scan(age_threshold_days=args.days)
    installers = data["installers"]

    if not installers:
        print(f"{GREEN}✨ No heavy installers (.dmg, .pkg, .iso) found! Your system is clean.{RESET}\n")
        return

    print(f"{BOLD}💾 Disk Bloat Analysis:{RESET}")
    print(f"  • Total installers found: {CYAN}{data['total_count']}{RESET} ({YELLOW}{data['total_size']}{RESET})")
    print(f"  • Older than {args.days} days:       {RED}{BOLD}{data['reclaimable_count']}{RESET} ({RED}{BOLD}{data['reclaimable_size']} reclaimable{RESET})\n")

    for idx, item in enumerate(installers, 1):
        age_color = RED if item["is_old"] else GREEN
        trash_tag = f"{RED}[Recommend Trash]{RESET}" if item["is_old"] else f"{DIM}[Recent]{RESET}"
        print(f"  {DIM}{idx}.{RESET} {BOLD}{item['filename']}{RESET}")
        print(f"     Size: {YELLOW}{item['size_str']}{RESET} | Age: {age_color}{item['age_str']}{RESET} | {trash_tag}")

    print()

    # Determine default to trash
    old_items = [i for i in installers if i["is_old"]]
    if not old_items:
        print(f"{GREEN}All installers are recent (<{args.days} days old). Nothing to clean right now!{RESET}\n")
        return

    if not args.apply:
        prompt = f"Move {len(old_items)} old installers ({data['reclaimable_size']}) to macOS Trash? [y/N]: "
        choice = input(f"{BOLD}{prompt}{RESET}").strip().lower()
        if choice not in ['y', 'yes']:
            print(f"{DIM}Operation cancelled. No files were trashed.{RESET}\n")
            return

    paths_to_trash = [i["path"] for i in old_items]
    res = janitor.move_to_trash(paths_to_trash)
    print(f"\n{GREEN}{BOLD}✅ Moved {res['trashed_count']} files to macOS Trash!{RESET}")
    print(f"🎉 {BOLD}Reclaimed {res['reclaimed_size']}{RESET} of disk space.")
    print(f"{DIM}(Files are in ~/.Trash. Run 'python3 main.py janitor --undo' to restore anytime){RESET}\n")

