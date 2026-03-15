"""
Multi-source local portal: NewsAPI, GNews, master CSV, secondary raw samples.

Run:
    python3 scripts/portal/data_portal.py --port 3000

Open: http://127.0.0.1:3000
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.utils.io import read_csv

ROOT_DIR = Path(__file__).resolve().parents[2]
NEWSAPI_CSV = ROOT_DIR / "data" / "normalized" / "newsapi_sample_v0.csv"
GNEWS_CSV = ROOT_DIR / "data" / "normalized" / "gnews_sample_v0.csv"
MASTER_CSV = ROOT_DIR / "data" / "normalized" / "master" / "master_source_v0.csv"
RAW_NEWSAPI_DIR = ROOT_DIR / "data" / "raw" / "newsapi"
RAW_GNEWS_DIR = ROOT_DIR / "data" / "raw" / "gnews"
SECONDARY_DIR = ROOT_DIR / "data" / "raw" / "secondary"


def _latest_json(raw_dir: Path) -> dict:
    if not raw_dir.exists():
        return {"filename": None, "data": None}
    candidates = [p for p in raw_dir.glob("*.json") if p.is_file()]
    if not candidates:
        return {"filename": None, "data": None}
    latest = max(candidates, key=lambda p: p.stat().st_mtime)
    try:
        data = json.loads(latest.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        data = {"error": "Invalid JSON"}
    return {"filename": latest.name, "data": data}


def _read_json_file(path: Path) -> dict:
    if not path.exists():
        return {"filename": path.name, "data": None}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        data = {"error": "Invalid JSON"}
    return {"filename": path.name, "data": data}


_HTML = """\
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>SBB Risk Radar — Phase 1 Portal</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: Arial, sans-serif; margin: 24px; color: #1f2937;
           max-width: 100%; overflow-x: hidden; }
    h1 { margin: 0 0 4px 0; }
    h2 { margin: 28px 0 8px 0; font-size: 16px; }
    .muted { color: #6b7280; font-size: 13px; margin-bottom: 8px; }
    .toolbar { display: flex; gap: 8px; align-items: center; margin-bottom: 12px; flex-wrap: wrap; }
    input  { padding: 7px 10px; min-width: 280px; border: 1px solid #d1d5db;
             border-radius: 4px; font-size: 14px; }
    button { padding: 7px 14px; cursor: pointer; border: 1px solid #d1d5db;
             border-radius: 4px; background: #f9fafb; font-size: 14px; }
    button:hover { background: #e5e7eb; }
    .badge { font-size: 12px; color: #6b7280; }
    table  { width: 100%; border-collapse: collapse; font-size: 13px; table-layout: fixed; }
    th, td { border: 1px solid #e5e7eb; padding: 6px 8px; vertical-align: top;
             text-align: left; overflow-wrap: anywhere; word-break: break-word; }
    th { background: #f9fafb; position: sticky; top: 0; }
    .scroll { max-height: 38vh; overflow: auto; border: 1px solid #e5e7eb; border-radius: 4px; }
    .grid2 { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
    .card  { border: 1px solid #e5e7eb; border-radius: 8px; padding: 14px; min-width: 0; }
    pre    { margin: 0; white-space: pre-wrap; overflow-wrap: anywhere;
             word-break: break-word; font-size: 12px; }
    @media (max-width: 960px) { .grid2 { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <h1>SBB Risk Radar — Phase 1 Portal</h1>
  <div class="muted">NewsAPI · GNews · Master CSV · Secondary raw samples</div>

  <div class="toolbar">
    <button id="refreshBtn">Refresh</button>
    <input id="searchInput" placeholder="Filter by title / source / query…" />
    <span id="newsapiCount" class="badge"></span>
    <span id="gnewsCount"  class="badge"></span>
    <span id="masterCount" class="badge"></span>
  </div>

  <!-- Normalized tables -->
  <div class="grid2">
    <div class="card">
      <h2>NewsAPI <span class="muted">newsapi_sample_v0.csv</span></h2>
      <div class="scroll">
        <table id="newsapiTable">
          <thead><tr>
            <th>source</th><th>author</th><th>title</th>
            <th>description</th><th>url</th><th>published_at</th><th>query</th>
          </tr></thead>
          <tbody></tbody>
        </table>
      </div>
    </div>
    <div class="card">
      <h2>GNews <span class="muted">gnews_sample_v0.csv</span></h2>
      <div class="scroll">
        <table id="gnewsTable">
          <thead><tr>
            <th>source</th><th>title</th><th>description</th>
            <th>url</th><th>published_at</th><th>query</th>
          </tr></thead>
          <tbody></tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- Master CSV -->
  <h2>Master Excel Format <span class="muted">master/master_source_v0.csv</span></h2>
  <div class="card">
    <div class="scroll">
      <table id="masterTable">
        <thead><tr>
          <th>record_id</th><th>source_name</th><th>title_raw</th>
          <th>document_url</th><th>published_at</th><th>batch_id</th>
        </tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </div>

  <!-- Secondary raw responses -->
  <h2>Secondary Raw Responses</h2>
  <div class="grid2">
    <div class="card">
      <div class="muted">Newsdata — <code id="newsdataFile"></code></div>
      <div class="scroll"><pre id="newsdataRaw"></pre></div>
    </div>
    <div class="card">
      <div class="muted">Mediastack — <code id="mediastackFile"></code></div>
      <div class="scroll"><pre id="mediastackRaw"></pre></div>
    </div>
  </div>

  <!-- Latest raw JSON snapshots -->
  <h2>Latest Raw JSON Snapshots</h2>
  <div class="grid2">
    <div class="card">
      <div class="muted">NewsAPI — <code id="newsapiRawFile"></code></div>
      <div class="scroll"><pre id="newsapiRaw"></pre></div>
    </div>
    <div class="card">
      <div class="muted">GNews — <code id="gnewsRawFile"></code></div>
      <div class="scroll"><pre id="gnewsRaw"></pre></div>
    </div>
  </div>

  <script>
    /* ── helpers ── */
    function esc(v) {
      return String(v ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }

    function truncate(value) {
      const s = JSON.stringify(value ?? {}, null, 2);
      return s.length > 14000 ? s.slice(0, 14000) + "\\n…truncated…" : s;
    }

    async function get(url) {
      return (await fetch(url)).json();
    }

    /* ── state ── */
    let newsapiRows = [], gnewsRows = [], masterRows = [];

    /* ── render ── */
    function renderTables() {
      const q = document.getElementById("searchInput").value.trim().toLowerCase();

      function matches(fields) {
        return !q || fields.join(" ").toLowerCase().includes(q);
      }

      const na = newsapiRows.filter(r => matches([r.source_name, r.author, r.title, r.description, r.query]));
      document.querySelector("#newsapiTable tbody").innerHTML = na.map(r => `<tr>
        <td>${esc(r.source_name)}</td><td>${esc(r.author)}</td><td>${esc(r.title)}</td>
        <td>${esc(r.description)}</td>
        <td><a href="${esc(r.url)}" target="_blank" rel="noreferrer">link</a></td>
        <td>${esc(r.published_at)}</td><td>${esc(r.query)}</td>
      </tr>`).join("");
      document.getElementById("newsapiCount").textContent = `NewsAPI: ${na.length}/${newsapiRows.length}`;

      const gn = gnewsRows.filter(r => matches([r.source_name, r.title, r.description, r.query]));
      document.querySelector("#gnewsTable tbody").innerHTML = gn.map(r => `<tr>
        <td>${esc(r.source_name)}</td><td>${esc(r.title)}</td>
        <td>${esc(r.description)}</td>
        <td><a href="${esc(r.url)}" target="_blank" rel="noreferrer">link</a></td>
        <td>${esc(r.published_at)}</td><td>${esc(r.query)}</td>
      </tr>`).join("");
      document.getElementById("gnewsCount").textContent = `GNews: ${gn.length}/${gnewsRows.length}`;

      const ms = masterRows.filter(r => matches([r.record_id, r.source_name, r.title_raw, r.batch_id]));
      document.querySelector("#masterTable tbody").innerHTML = ms.map(r => `<tr>
        <td>${esc(r.record_id)}</td><td>${esc(r.source_name)}</td><td>${esc(r.title_raw)}</td>
        <td><a href="${esc(r.document_url)}" target="_blank" rel="noreferrer">link</a></td>
        <td>${esc(r.published_at)}</td><td>${esc(r.batch_id)}</td>
      </tr>`).join("");
      document.getElementById("masterCount").textContent = `Master: ${ms.length}/${masterRows.length}`;
    }

    /* ── load ── */
    async function loadAll() {
      const [na, gn, naRaw, gnRaw, ndRaw, msRaw, master] = await Promise.all([
        get("/api/articles/newsapi"),
        get("/api/articles/gnews"),
        get("/api/raw/newsapi/latest"),
        get("/api/raw/gnews/latest"),
        get("/api/raw/secondary/newsdata"),
        get("/api/raw/secondary/mediastack"),
        get("/api/articles/master"),
      ]);

      newsapiRows = na.articles || [];
      gnewsRows   = gn.articles || [];
      masterRows  = master.articles || [];
      renderTables();

      document.getElementById("newsapiRawFile").textContent  = naRaw.filename  || "n/a";
      document.getElementById("gnewsRawFile").textContent    = gnRaw.filename   || "n/a";
      document.getElementById("newsdataFile").textContent    = ndRaw.filename   || "n/a";
      document.getElementById("mediastackFile").textContent  = msRaw.filename   || "n/a";

      document.getElementById("newsapiRaw").textContent  = truncate(naRaw.data);
      document.getElementById("gnewsRaw").textContent    = truncate(gnRaw.data);
      document.getElementById("newsdataRaw").textContent  = truncate(ndRaw.data);
      document.getElementById("mediastackRaw").textContent = truncate(msRaw.data);
    }

    document.getElementById("refreshBtn").addEventListener("click", loadAll);
    document.getElementById("searchInput").addEventListener("input", renderTables);
    loadAll();
  </script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def _json(self, status: int, payload: object) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, status: int, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        p = urlparse(self.path).path
        if p == "/":
            self._html(200, _HTML)
        elif p == "/api/health":
            self._json(200, {"status": "ok"})
        elif p == "/api/articles/newsapi":
            self._json(200, {"articles": read_csv(NEWSAPI_CSV)})
        elif p == "/api/articles/gnews":
            self._json(200, {"articles": read_csv(GNEWS_CSV)})
        elif p == "/api/articles/master":
            self._json(200, {"articles": read_csv(MASTER_CSV)})
        elif p == "/api/raw/newsapi/latest":
            self._json(200, _latest_json(RAW_NEWSAPI_DIR))
        elif p == "/api/raw/gnews/latest":
            self._json(200, _latest_json(RAW_GNEWS_DIR))
        elif p == "/api/raw/secondary/newsdata":
            self._json(200, _read_json_file(SECONDARY_DIR / "newsdata_sample_response.json"))
        elif p == "/api/raw/secondary/mediastack":
            self._json(200, _read_json_file(SECONDARY_DIR / "mediastack_sample_response.json"))
        else:
            self._json(404, {"error": "Not found"})

    def log_message(self, *args) -> None:  # silence per-request logs
        return


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve Phase 1 multi-source data portal.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3000)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Portal → http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
