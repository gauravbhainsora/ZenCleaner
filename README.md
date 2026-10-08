# 🧹 ZenCleaner for macOS

> **Zero-Effort, Safe Desktop & Downloads Organizer**  
> Clean up gigabytes of loose screenshots, installers, and documents in seconds with instant Undo protection.

---

## 🌟 Key Features

* **🛡️ 100% Safe (Dry-Run by Default):** Never moves a file without your confirmation unless you explicitly pass `--apply`.
* **↩️ One-Click Undo:** Every move is logged in a local transaction ledger (`~/.zencleaner/history.json`). Run `python3 main.py undo` to restore files right back to their exact original locations.
* **🧠 Context-Aware Smart Categorization:**
  * **Screenshots:** Automatically grouped by Year & Month (e.g. `Organized/Screenshots/2026-09/`).
  * **Financial & Receipts:** Invoices, payslips, bills, and tax documents detected and grouped together.
  * **Disk Images & Installers:** `.dmg`, `.pkg`, `.iso` separated so you can reclaim gigabytes of disk space.
  * **Documents & Reading:** PDFs, books, and study materials.
  * **Office Files:** Spreadsheets, presentations, and `.docx` files.
  * **Media:** Audio, video recordings, and images separated into dedicated folders.
  * **Developer Code:** Scripts, notebooks, configs, and JSON.
* **⚡ Zero Dependencies:** Built entirely with Python 3's standard library. No pip installs, virtualenvs, or external packages required.
* **🖥️ Dual Interfaces:** Fast colored CLI **and** an interactive browser dashboard.

---

## 🚀 Quick Usage

### 1. Terminal (CLI)

```bash
# Preview what would be organized on Desktop (Dry run)
python3 main.py scan desktop

# Preview what would be organized in Downloads (Dry run)
python3 main.py scan downloads

# Organize Desktop (prompts for confirmation before moving)
python3 main.py clean desktop

# Organize Downloads directly without prompt
python3 main.py clean downloads --apply

# Undo the last cleanup session (reverts all moved files)
python3 main.py undo

# View lifetime cleanup stats
python3 main.py stats

# Reclaim disk space (preview old installers >14 days)
python3 main.py janitor

# Move old installers directly to macOS Trash
python3 main.py janitor --apply

# Undo the last trashing session (moves files out of Trash)
python3 main.py janitor --undo
```

---

### 2. Interactive Web Dashboard

Launch the local web dashboard:

```bash
python3 main.py ui
```

Then open **[http://localhost:5050](http://localhost:5050)** in your browser.

* Switch between **Desktop** and **Downloads** tabs.
* See real-time clutter count and storage footprint.
* Review detected categories with badges.
* Check/uncheck individual files before organizing.
* One-click **Clean & Organize** or **Undo Last**.

---

## 🛡️ Safety & Collision Protections

1. **Active Download Protection:** Files modified in the last 60 seconds (or having `.crdownload`, `.part`, `.download` extensions) are automatically skipped.
2. **Hidden Files Protection:** `.DS_Store`, `.localized`, and dotfiles are untouched.
3. **No Overwrites:** If a file with the same name already exists in the destination folder, ZenCleaner automatically appends `(1)`, `(2)`, etc.
4. **Isolated Organization:** Files are neatly arranged into an `Organized/` folder inside the target directory, keeping your existing folders intact.
