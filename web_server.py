"""
ZenCleaner - Built-in Local Web Server & Dashboard
Provides a modern, lightweight GUI for organizing Desktop/Downloads and reclaiming disk space with Disk Janitor.
Uses standard library http.server and urllib. Zero external dependencies!
"""

import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from cleaner import ZenCleaner
from janitor import InstallerJanitor

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ZenCleaner - Desktop, Downloads & Disk Janitor</title>
  <style>
    :root {
      --bg: #0f172a;
      --card-bg: #1e293b;
      --card-border: #334155;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --accent: #38bdf8;
      --accent-hover: #0284c7;
      --accent-green: #10b981;
      --accent-red: #ef4444;
      --accent-purple: #a855f7;
      --accent-amber: #f59e0b;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
      padding: 30px 20px;
    }
    .container {
      max-width: 1080px;
      margin: 0 auto;
    }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--card-border);
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .brand-icon {
      font-size: 32px;
      background: #1e293b;
      padding: 8px 12px;
      border-radius: 12px;
      border: 1px solid var(--card-border);
    }
    h1 { font-size: 24px; font-weight: 700; }
    p.subtitle { color: var(--text-muted); font-size: 14px; }
    .tabs {
      display: flex;
      background: #1e293b;
      border-radius: 10px;
      padding: 4px;
      gap: 4px;
      border: 1px solid var(--card-border);
    }
    .tab-btn {
      padding: 8px 18px;
      background: transparent;
      border: none;
      color: var(--text-muted);
      cursor: pointer;
      border-radius: 8px;
      font-weight: 600;
      font-size: 14px;
      transition: all 0.2s;
    }
    .tab-btn.active {
      background: var(--accent);
      color: #0f172a;
    }
    .tab-btn.active-janitor {
      background: var(--accent-amber);
      color: #0f172a;
    }
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }
    .stat-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      padding: 20px;
      border-radius: 14px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .stat-label { font-size: 13px; color: var(--text-muted); font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }
    .stat-value { font-size: 28px; font-weight: 700; margin-top: 6px; }
    
    .action-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      padding: 16px 20px;
      border-radius: 14px;
      margin-bottom: 20px;
    }
    .action-left {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .btn {
      padding: 10px 20px;
      border-radius: 10px;
      border: none;
      font-weight: 600;
      font-size: 14px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      transition: opacity 0.2s, transform 0.1s;
    }
    .btn:hover { opacity: 0.9; }
    .btn:active { transform: scale(0.98); }
    .btn-primary { background: var(--accent); color: #0f172a; }
    .btn-danger { background: var(--accent-red); color: #fff; }
    .btn-secondary { background: #334155; color: var(--text); }
    .btn-undo { background: var(--accent-purple); color: #fff; }

    .file-table-wrapper {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 14px;
      overflow: hidden;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      text-align: left;
    }
    th, td {
      padding: 14px 18px;
      border-bottom: 1px solid var(--card-border);
      font-size: 14px;
    }
    th {
      background: #182234;
      color: var(--text-muted);
      font-weight: 600;
      text-transform: uppercase;
      font-size: 12px;
      letter-spacing: 0.5px;
    }
    tr:last-child td { border-bottom: none; }
    tr:hover { background: #26334d; }
    .badge {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
    }
    .badge-screenshots { background: rgba(56, 189, 248, 0.2); color: #38bdf8; }
    .badge-receipts { background: rgba(16, 185, 129, 0.2); color: #10b981; }
    .badge-installers { background: rgba(245, 158, 11, 0.2); color: #f59e0b; }
    .badge-documents { background: rgba(168, 85, 247, 0.2); color: #c084fc; }
    .badge-audio { background: rgba(236, 72, 153, 0.2); color: #f472b6; }
    .badge-code { background: rgba(34, 197, 94, 0.2); color: #4ade80; }
    .badge-other { background: rgba(148, 163, 184, 0.2); color: #cbd5e1; }
    .badge-old { background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.4); }
    .badge-recent { background: rgba(16, 185, 129, 0.2); color: #10b981; }
    
    .dest-path {
      color: var(--text-muted);
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 12px;
    }
    .dest-highlight { color: #38bdf8; }
    .toast {
      position: fixed;
      bottom: 24px;
      right: 24px;
      padding: 14px 22px;
      background: #1e293b;
      border: 1px solid var(--card-border);
      border-radius: 10px;
      color: var(--text);
      box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
      display: none;
      z-index: 100;
    }
    .empty-state {
      padding: 60px 20px;
      text-align: center;
      color: var(--text-muted);
    }
    .empty-icon { font-size: 48px; margin-bottom: 12px; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="brand">
        <div class="brand-icon">🧹</div>
        <div>
          <h1>ZenCleaner</h1>
          <p class="subtitle">Zero-Effort Mac Desktop, Downloads & Disk Janitor</p>
        </div>
      </div>
      <div class="tabs">
        <button class="tab-btn active" id="tabDesktop" onclick="switchFolder('desktop')">Desktop</button>
        <button class="tab-btn" id="tabDownloads" onclick="switchFolder('downloads')">Downloads</button>
        <button class="tab-btn" id="tabJanitor" onclick="switchFolder('janitor')" style="display: flex; align-items: center; gap: 6px;">
          <span>💾 Disk Janitor</span>
          <span id="janitorBadge" style="font-size: 11px; background: rgba(245, 158, 11, 0.3); color: #f59e0b; padding: 2px 6px; border-radius: 10px;">...</span>
        </button>
      </div>
    </header>

    <div class="stats-grid" id="statsGrid">
      <div class="stat-card">
        <div class="stat-label" id="lblCard1">Loose Files Found</div>
        <div class="stat-value" id="statFiles">0</div>
      </div>
      <div class="stat-card">
        <div class="stat-label" id="lblCard2">Total Size</div>
        <div class="stat-value" id="statSize" style="color: var(--accent-amber);">0 MB</div>
      </div>
      <div class="stat-card">
        <div class="stat-label" id="lblCard3">Top Category</div>
        <div class="stat-value" id="statTopCat" style="color: var(--accent);">-</div>
      </div>
      <div class="stat-card">
        <div class="stat-label" id="lblCard4">Safety Status</div>
        <div class="stat-value" id="statSafety" style="color: var(--accent-green); font-size: 18px; line-height: 34px;">🛡️ Safe (Undo Ready)</div>
      </div>
    </div>

    <div class="action-bar">
      <div class="action-left">
        <input type="checkbox" id="selectAll" checked onchange="toggleSelectAll(this)" style="transform: scale(1.2); cursor: pointer;">
        <label for="selectAll" style="font-weight: 600; cursor: pointer;">Select All (<span id="selectedCount">0</span> selected)</label>
      </div>
      <div style="display: flex; gap: 10px;">
        <button class="btn btn-secondary" onclick="refreshCurrentView()">🔄 Refresh</button>
        <button class="btn btn-undo" id="btnUndo" onclick="executeUndo()">↩️ Undo Last</button>
        <button class="btn btn-primary" id="btnPrimary" onclick="executePrimaryAction()">🚀 Clean & Organize</button>
      </div>
    </div>

    <div class="file-table-wrapper">
      <table id="fileTable">
        <thead id="tableHead">
          <tr>
            <th style="width: 40px;"></th>
            <th>File Name</th>
            <th>Category</th>
            <th>Size</th>
            <th>New Destination</th>
          </tr>
        </thead>
        <tbody id="fileListBody">
          <!-- Populated by JS -->
        </tbody>
      </table>
      <div id="emptyState" class="empty-state" style="display: none;">
        <div class="empty-icon">✨</div>
        <h3 id="emptyTitle">Everything is pristine!</h3>
        <p id="emptyMsg">No loose files found in this folder.</p>
      </div>
    </div>
  </div>

  <div id="toast" class="toast"></div>

  <script>
    let currentTarget = 'desktop';
    let currentMoves = [];
    let currentInstallers = [];

    function showToast(msg, color='#38bdf8') {
      const toast = document.getElementById('toast');
      toast.innerText = msg;
      toast.style.borderColor = color;
      toast.style.display = 'block';
      setTimeout(() => { toast.style.display = 'none'; }, 4000);
    }

    function switchFolder(folder) {
      currentTarget = folder;
      document.getElementById('tabDesktop').className = 'tab-btn ' + (folder === 'desktop' ? 'active' : '');
      document.getElementById('tabDownloads').className = 'tab-btn ' + (folder === 'downloads' ? 'active' : '');
      document.getElementById('tabJanitor').className = 'tab-btn ' + (folder === 'janitor' ? 'active-janitor' : '');

      refreshCurrentView();
    }

    function refreshCurrentView() {
      if (currentTarget === 'janitor') {
        fetchJanitor();
      } else {
        fetchScan();
      }
      updateJanitorBadge();
    }

    async function updateJanitorBadge() {
      try {
        const res = await fetch('/api/installers');
        const data = await res.json();
        const badge = document.getElementById('janitorBadge');
        if (data.reclaimable_count > 0) {
          badge.innerText = data.reclaimable_size;
          badge.style.display = 'inline-block';
        } else {
          badge.innerText = '0 B';
        }
      } catch (e) {}
    }

    function getBadgeClass(cat) {
      const lower = cat.toLowerCase();
      if (lower.includes('screenshot')) return 'badge-screenshots';
      if (lower.includes('receipt') || lower.includes('invoice') || lower.includes('financial')) return 'badge-receipts';
      if (lower.includes('installer')) return 'badge-installers';
      if (lower.includes('document') || lower.includes('office')) return 'badge-documents';
      if (lower.includes('audio')) return 'badge-audio';
      if (lower.includes('code') || lower.includes('dev')) return 'badge-code';
      return 'badge-other';
    }

    async function fetchScan() {
      // Update UI for Cleaner mode
      document.getElementById('lblCard1').innerText = 'Loose Files Found';
      document.getElementById('lblCard2').innerText = 'Total Clutter Size';
      document.getElementById('lblCard3').innerText = 'Top Category';
      document.getElementById('lblCard4').innerText = 'Safety Status';
      document.getElementById('statSafety').innerText = '🛡️ Safe (Undo Ready)';
      document.getElementById('statSafety').style.color = 'var(--accent-green)';
      document.getElementById('btnPrimary').className = 'btn btn-primary';
      document.getElementById('btnPrimary').innerText = '🚀 Clean & Organize';
      document.getElementById('btnUndo').innerText = '↩️ Undo Last';

      document.getElementById('tableHead').innerHTML = `
        <tr>
          <th style="width: 40px;"></th>
          <th>File Name</th>
          <th>Category</th>
          <th>Size</th>
          <th>New Destination</th>
        </tr>
      `;

      try {
        const res = await fetch('/api/scan?target=' + currentTarget);
        const data = await res.json();
        currentMoves = data.moves || [];
        renderCleanerFiles();
      } catch (e) {
        showToast('Error loading scan: ' + e, '#ef4444');
      }
    }

    function renderCleanerFiles() {
      const tbody = document.getElementById('fileListBody');
      const emptyState = document.getElementById('emptyState');
      const table = document.getElementById('fileTable');
      tbody.innerHTML = '';

      if (currentMoves.length === 0) {
        table.style.display = 'none';
        emptyState.style.display = 'block';
        document.getElementById('emptyTitle').innerText = 'Everything is pristine!';
        document.getElementById('emptyMsg').innerText = `No loose files found in ${currentTarget}.`;
        document.getElementById('statFiles').innerText = '0';
        document.getElementById('statSize').innerText = '0 MB';
        document.getElementById('statTopCat').innerText = 'None';
        document.getElementById('selectedCount').innerText = '0';
        return;
      }

      table.style.display = 'table';
      emptyState.style.display = 'none';

      let totalBytes = 0;
      const catCount = {};

      currentMoves.forEach((move, idx) => {
        totalBytes += move.size_bytes;
        catCount[move.category] = (catCount[move.category] || 0) + 1;

        const row = document.createElement('tr');
        row.innerHTML = `
          <td><input type="checkbox" data-idx="${idx}" class="file-chk" checked onchange="updateSelectedCount()" style="transform: scale(1.1); cursor: pointer;"></td>
          <td style="font-weight: 500;">${escapeHtml(move.filename)}</td>
          <td><span class="badge ${getBadgeClass(move.category)}">${escapeHtml(move.category)}</span></td>
          <td style="color: var(--text-muted);">${move.size_str}</td>
          <td class="dest-path">Organized/<span class="dest-highlight">${escapeHtml(move.relative_folder)}</span>/</td>
        `;
        tbody.appendChild(row);
      });

      document.getElementById('statFiles').innerText = currentMoves.length;
      document.getElementById('statSize').innerText = (totalBytes / (1024 * 1024)).toFixed(1) + ' MB';
      
      const topCat = Object.entries(catCount).sort((a,b) => b[1] - a[1])[0];
      document.getElementById('statTopCat').innerText = topCat ? topCat[0] : 'None';
      
      updateSelectedCount();
    }

    async function fetchJanitor() {
      // Update UI for Janitor mode
      document.getElementById('lblCard1').innerText = 'Installers Found';
      document.getElementById('lblCard2').innerText = 'Reclaimable Space';
      document.getElementById('lblCard3').innerText = 'Total Installer Size';
      document.getElementById('lblCard4').innerText = 'Trash Safety';
      document.getElementById('statSafety').innerText = '🗑️ Moves to macOS Trash';
      document.getElementById('statSafety').style.color = 'var(--accent-amber)';
      document.getElementById('btnPrimary').className = 'btn btn-danger';
      document.getElementById('btnPrimary').innerText = '🗑️ Move Selected to Trash';
      document.getElementById('btnUndo').innerText = '↩️ Undo Trashing';

      document.getElementById('tableHead').innerHTML = `
        <tr>
          <th style="width: 40px;"></th>
          <th>Installer Name</th>
          <th>Size</th>
          <th>Age</th>
          <th>Status / Recommendation</th>
        </tr>
      `;

      try {
        const res = await fetch('/api/installers');
        const data = await res.json();
        currentInstallers = data.installers || [];
        renderJanitorFiles(data);
      } catch (e) {
        showToast('Error loading installers: ' + e, '#ef4444');
      }
    }

    function renderJanitorFiles(data) {
      const tbody = document.getElementById('fileListBody');
      const emptyState = document.getElementById('emptyState');
      const table = document.getElementById('fileTable');
      tbody.innerHTML = '';

      if (currentInstallers.length === 0) {
        table.style.display = 'none';
        emptyState.style.display = 'block';
        document.getElementById('emptyTitle').innerText = 'Zero Disk Bloat!';
        document.getElementById('emptyMsg').innerText = 'No heavy .dmg, .pkg, or .iso installers found.';
        document.getElementById('statFiles').innerText = '0';
        document.getElementById('statSize').innerText = '0 B';
        document.getElementById('statTopCat').innerText = '0 B';
        document.getElementById('selectedCount').innerText = '0';
        return;
      }

      table.style.display = 'table';
      emptyState.style.display = 'none';

      document.getElementById('statFiles').innerText = data.total_count;
      document.getElementById('statSize').innerText = data.reclaimable_size;
      document.getElementById('statTopCat').innerText = data.total_size;

      currentInstallers.forEach((item, idx) => {
        const isChecked = item.recommended_trash;
        const row = document.createElement('tr');
        row.innerHTML = `
          <td><input type="checkbox" data-idx="${idx}" class="file-chk" ${isChecked ? 'checked' : ''} onchange="updateSelectedCount()" style="transform: scale(1.1); cursor: pointer;"></td>
          <td style="font-weight: 500;">${escapeHtml(item.filename)}</td>
          <td style="color: var(--accent-amber); font-weight: 600;">${item.size_str}</td>
          <td style="color: var(--text-muted);">${item.age_str}</td>
          <td>
            <span class="badge ${item.is_old ? 'badge-old' : 'badge-recent'}">
              ${item.is_old ? '⚠️ Old (>14d) - Recommend Trash' : '✅ Recent (<14d)'}
            </span>
          </td>
        `;
        tbody.appendChild(row);
      });

      updateSelectedCount();
    }

    function escapeHtml(text) {
      const div = document.createElement('div');
      div.innerText = text;
      return div.innerHTML;
    }

    function toggleSelectAll(master) {
      document.querySelectorAll('.file-chk').forEach(c => c.checked = master.checked);
      updateSelectedCount();
    }

    function updateSelectedCount() {
      const checked = document.querySelectorAll('.file-chk:checked').length;
      document.getElementById('selectedCount').innerText = checked;
      document.getElementById('btnPrimary').disabled = checked === 0;
    }

    async function executePrimaryAction() {
      if (currentTarget === 'janitor') {
        executeTrash();
      } else {
        executeClean();
      }
    }

    async function executeClean() {
      const selectedIndices = Array.from(document.querySelectorAll('.file-chk:checked')).map(c => parseInt(c.dataset.idx));
      if (selectedIndices.length === 0) return;

      const movesToExecute = selectedIndices.map(i => currentMoves[i]);
      const btn = document.getElementById('btnPrimary');
      btn.innerText = '⏳ Organizing...';
      btn.disabled = true;

      try {
        const res = await fetch('/api/clean?target=' + currentTarget, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ moves: movesToExecute })
        });
        const data = await res.json();
        showToast(`🎉 Cleaned ${data.moved_count} files (${data.total_size})!`, '#10b981');
        refreshCurrentView();
      } catch (e) {
        showToast('Error organizing files: ' + e, '#ef4444');
      } finally {
        btn.innerText = '🚀 Clean & Organize';
        btn.disabled = false;
      }
    }

    async function executeTrash() {
      const selectedIndices = Array.from(document.querySelectorAll('.file-chk:checked')).map(c => parseInt(c.dataset.idx));
      if (selectedIndices.length === 0) return;

      const pathsToTrash = selectedIndices.map(i => currentInstallers[i].path);
      const totalSize = selectedIndices.map(i => currentInstallers[i].size_bytes).reduce((a,b)=>a+b, 0);
      const sizeStr = (totalSize / (1024 * 1024)).toFixed(1) + ' MB';

      if (!confirm(`Move ${pathsToTrash.length} installers (${sizeStr}) to macOS Trash? You can restore them anytime.`)) return;

      const btn = document.getElementById('btnPrimary');
      btn.innerText = '⏳ Moving to Trash...';
      btn.disabled = true;

      try {
        const res = await fetch('/api/installers/trash', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ paths: pathsToTrash })
        });
        const data = await res.json();
        showToast(`🗑️ Moved ${data.trashed_count} installers (${data.reclaimed_size}) to Trash!`, '#f59e0b');
        refreshCurrentView();
      } catch (e) {
        showToast('Error trashing files: ' + e, '#ef4444');
      } finally {
        btn.innerText = '🗑️ Move Selected to Trash';
        btn.disabled = false;
      }
    }

    async function executeUndo() {
      if (currentTarget === 'janitor') {
        if (!confirm('Restore the most recently trashed installers back to their original folder?')) return;
        try {
          const res = await fetch('/api/installers/undo', { method: 'POST' });
          const data = await res.json();
          if (data.success) {
            showToast(`↩️ Restored ${data.restored_count} installers from Trash!`, '#a855f7');
            refreshCurrentView();
          } else {
            showToast(data.message, '#ef4444');
          }
        } catch (e) {
          showToast('Error restoring: ' + e, '#ef4444');
        }
      } else {
        if (!confirm('Undo the most recent cleanup session and move files back?')) return;
        try {
          const res = await fetch('/api/undo', { method: 'POST' });
          const data = await res.json();
          if (data.success) {
            showToast(`↩️ Restored ${data.restored_count} files!`, '#a855f7');
            refreshCurrentView();
          } else {
            showToast(data.message, '#ef4444');
          }
        } catch (e) {
          showToast('Error undoing: ' + e, '#ef4444');
        }
      }
    }

    refreshCurrentView();
  </script>
</body>
</html>
"""

class ZenServerHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode("utf-8"))
            return

        if path == "/api/scan":
            target_str = params.get("target", ["desktop"])[0]
            target_path = Path.home() / ("Desktop" if target_str == "desktop" else "Downloads")
            cleaner = ZenCleaner(target_path)
            moves = cleaner.scan()
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"moves": moves}).encode("utf-8"))
            return

        if path == "/api/installers":
            janitor = InstallerJanitor()
            data = janitor.scan(age_threshold_days=14)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        if path == "/api/stats":
            stats = ZenCleaner.get_stats()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(stats).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else "{}"

        if path == "/api/clean":
            target_str = params.get("target", ["desktop"])[0]
            target_path = Path.home() / ("Desktop" if target_str == "desktop" else "Downloads")
            cleaner = ZenCleaner(target_path)
            
            payload = json.loads(body)
            moves = payload.get("moves") or cleaner.scan()
            result = cleaner.execute_plan(moves)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode("utf-8"))
            return

        if path == "/api/installers/trash":
            payload = json.loads(body)
            paths = payload.get("paths", [])
            janitor = InstallerJanitor()
            result = janitor.move_to_trash(paths)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode("utf-8"))
            return

        if path == "/api/installers/undo":
            result = InstallerJanitor.undo_last_trash()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode("utf-8"))
            return

        if path == "/api/undo":
            result = ZenCleaner.undo_last_session()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

def run_web_dashboard(port: int = 5050):
    server = HTTPServer(('127.0.0.1', port), ZenServerHandler)
    url = f"http://localhost:{port}"
    print(f"\n🚀 \033[1m\033[36mZenCleaner Web Dashboard running at:\033[0m \033[32m{url}\033[0m")
    print(f"👉 Open this link in your browser to organize your Desktop & Downloads visually!")
    print(f"Press \033[33mCtrl+C\033[0m to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping dashboard server...")
        server.server_close()
