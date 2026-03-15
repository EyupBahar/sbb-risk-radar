"""
Tiny local portal to compare multi-provider news outputs on localhost.

Run:
    python3 scripts/portal/newsapi_portal.py --port 3000
"""

from __future__ import annotations

import argparse
import csv
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT_DIR = Path(__file__).resolve().parents[2]
NEWSAPI_CSV_PATH = ROOT_DIR / "data" / "normalized" / "newsapi_sample_v0.csv"
GNEWS_CSV_PATH = ROOT_DIR / "data" / "normalized" / "gnews_sample_v0.csv"
MASTER_CSV_PATH = ROOT_DIR / "data" / "normalized" / "master" / "master_source_v0.csv"
RAW_NEWSAPI_DIR = ROOT_DIR / "data" / "raw" / "newsapi"
RAW_GNEWS_DIR = ROOT_DIR / "data" / "raw" / "gnews"
SECONDARY_DIR = ROOT_DIR / "data" / "raw" / "secondary"


def read_csv_rows(csv_path: Path) -> list[dict[str, str]]:
    if not csv_path.exists():
        return []
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


def read_latest_json(raw_dir: Path) -> dict[str, object]:
    if not raw_dir.exists():
        return {"filename": None, "data": None}
    candidates = [p for p in raw_dir.glob("*.json") if p.is_file()]
    if not candidates:
        return {"filename": None, "data": None}
    latest = max(candidates, key=lambda p: p.stat().st_mtime)
    try:
        payload = json.loads(latest.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        payload = {"error": "Invalid JSON file content"}
    return {"filename": latest.name, "data": payload}


def read_json_file(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"filename": path.name, "data": None}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        payload = {"error": "Invalid JSON file content"}
    return {"filename": path.name, "data": payload}


def build_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Multi-API News Portal</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: Arial, sans-serif; margin: 24px; color: #1f2937; max-width: 100%; overflow-x: hidden; }
    h1 { margin: 0 0 8px 0; }
    h2 { margin: 24px 0 8px 0; }
    .muted { color: #6b7280; margin-bottom: 8px; }
    .row { display: flex; gap: 8px; align-items: center; margin-bottom: 12px; }
    input { padding: 8px; min-width: 260px; }
    button { padding: 8px 12px; cursor: pointer; }
    table { width: 100%; border-collapse: collapse; font-size: 14px; table-layout: fixed; }
    th, td { border: 1px solid #e5e7eb; padding: 8px; vertical-align: top; text-align: left; overflow-wrap: anywhere; word-break: break-word; }
    th { background: #f9fafb; position: sticky; top: 0; }
    .wrap { max-height: 72vh; overflow: auto; border: 1px solid #e5e7eb; }
    .wrap-sm { max-height: 36vh; overflow: auto; border: 1px solid #e5e7eb; }
    .small { font-size: 12px; color: #6b7280; }
    .grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
    .card { border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; min-width: 0; }
    pre { margin: 0; white-space: pre-wrap; overflow-wrap: anywhere; word-break: break-word; font-size: 12px; }
    @media (max-width: 1100px) { .grid { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <h1>Multi-API Local Portal</h1>
  <div class="muted">Compare outputs from NewsAPI, GNews, Newsdata, and Mediastack</div>
  <div class="row">
    <button id="refreshBtn">Refresh</button>
    <input id="searchInput" placeholder="Filter by title/source/query..." />
    <span id="newsapiCount" class="small"></span>
    <span id="gnewsCount" class="small"></span>
  </div>

  <div class="grid">
    <div class="card">
      <h2>NewsAPI (Normalized CSV)</h2>
      <div class="muted"><code>data/normalized/newsapi_sample_v0.csv</code></div>
      <div class="wrap-sm">
        <table id="newsapiTable">
          <thead>
            <tr>
              <th>source_name</th>
              <th>author</th>
              <th>title</th>
              <th>description</th>
              <th>url</th>
              <th>published_at</th>
              <th>query</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </div>

    <div class="card">
      <h2>GNews (Normalized CSV)</h2>
      <div class="muted"><code>data/normalized/gnews_sample_v0.csv</code></div>
      <div class="wrap-sm">
        <table id="gnewsTable">
          <thead>
            <tr>
              <th>source_name</th>
              <th>title</th>
              <th>description</th>
              <th>url</th>
              <th>published_at</th>
              <th>query</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </div>
  </div>

  <h2>Master Excel Format (Deck)</h2>
  <div class="card" style="grid-column: 1 / -1;">
    <div class="muted"><code>data/normalized/master/master_source_v0.csv</code> — SBB_Risk_Radar_Master_Source_Template format</div>
    <div class="wrap-sm">
      <table id="masterTable">
        <thead>
          <tr>
            <th>record_id</th>
            <th>source_name</th>
            <th>title_raw</th>
            <th>document_url</th>
            <th>published_at</th>
            <th>batch_id</th>
          </tr>
        </thead>
        <tbody></tbody>
      </table>
    </div>
    <span id="masterCount" class="small"></span>
  </div>

  <h2>Secondary API Raw Responses (Separate)</h2>
  <div class="grid">
    <div class="card">
      <div class="muted">Newsdata sample: <code id="newsdataFile"></code></div>
      <div class="wrap-sm"><pre id="newsdataRaw"></pre></div>
    </div>
    <div class="card">
      <div class="muted">Mediastack sample: <code id="mediastackFile"></code></div>
      <div class="wrap-sm"><pre id="mediastackRaw"></pre></div>
    </div>
  </div>

  <h2>Latest Raw JSON Snapshots</h2>
  <div class="grid">
    <div class="card">
      <div class="muted">NewsAPI raw: <code id="newsapiRawFile"></code></div>
      <div class="wrap-sm"><pre id="newsapiRaw"></pre></div>
    </div>
    <div class="card">
      <div class="muted">GNews raw: <code id="gnewsRawFile"></code></div>
      <div class="wrap-sm"><pre id="gnewsRaw"></pre></div>
    </div>
  </div>

  <script>
    const newsapiTbody = document.querySelector("#newsapiTable tbody");
    const gnewsTbody = document.querySelector("#gnewsTable tbody");
    const searchInput = document.querySelector("#searchInput");
    const newsapiCountEl = document.querySelector("#newsapiCount");
    const gnewsCountEl = document.querySelector("#gnewsCount");
    let newsapiRows = [];
    let gnewsRows = [];
    let masterRows = [];

    function toCell(v) {
      return (v ?? "").toString();
    }

    function truncateJson(value) {
      const pretty = JSON.stringify(value ?? {}, null, 2);
      return pretty.length > 12000 ? pretty.slice(0, 12000) + "\\n...truncated..." : pretty;
    }

    function renderTables() {
      const q = searchInput.value.trim().toLowerCase();
      const filteredNewsapi = newsapiRows.filter(r => {
        if (!q) return true;
        return [r.source_name, r.author, r.title, r.description, r.query]
          .join(" ")
          .toLowerCase()
          .includes(q);
      });
      const filteredGnews = gnewsRows.filter(r => {
        if (!q) return true;
        return [r.source_name, r.title, r.description, r.query]
          .join(" ")
          .toLowerCase()
          .includes(q);
      });

      newsapiTbody.innerHTML = filteredNewsapi.map(r => `
        <tr>
          <td>${toCell(r.source_name)}</td>
          <td>${toCell(r.author)}</td>
          <td>${toCell(r.title)}</td>
          <td>${toCell(r.description)}</td>
          <td><a href="${toCell(r.url)}" target="_blank" rel="noreferrer">link</a></td>
          <td>${toCell(r.published_at)}</td>
          <td>${toCell(r.query)}</td>
        </tr>
      `).join("");
      gnewsTbody.innerHTML = filteredGnews.map(r => `
        <tr>
          <td>${toCell(r.source_name)}</td>
          <td>${toCell(r.title)}</td>
          <td>${toCell(r.description)}</td>
          <td><a href="${toCell(r.url)}" target="_blank" rel="noreferrer">link</a></td>
          <td>${toCell(r.published_at)}</td>
          <td>${toCell(r.query)}</td>
        </tr>
      `).join("");

      newsapiCountEl.textContent = `NewsAPI: ${filteredNewsapi.length} / ${newsapiRows.length}`;
      gnewsCountEl.textContent = `GNews: ${filteredGnews.length} / ${gnewsRows.length}`;

      const masterTbody = document.querySelector("#masterTable tbody");
      const masterCountEl = document.querySelector("#masterCount");
      const qm = searchInput.value.trim().toLowerCase();
      const filteredMaster = masterRows.filter(r => {
        if (!qm) return true;
        return [r.record_id, r.source_name, r.title_raw, r.document_url, r.batch_id]
          .join(" ")
          .toLowerCase()
          .includes(qm);
      });
      masterTbody.innerHTML = filteredMaster.map(r => `
        <tr>
          <td>${toCell(r.record_id)}</td>
          <td>${toCell(r.source_name)}</td>
          <td>${toCell(r.title_raw)}</td>
          <td><a href="${toCell(r.document_url)}" target="_blank" rel="noreferrer">link</a></td>
          <td>${toCell(r.published_at)}</td>
          <td>${toCell(r.batch_id)}</td>
        </tr>
      `).join("");
      masterCountEl.textContent = `Master: ${filteredMaster.length} / ${masterRows.length} rows`;
    }

    async function fetchJson(url) {
      const res = await fetch(url);
      return await res.json();
    }

    async function loadAll() {
      const [
        newsapiData,
        gnewsData,
        newsapiRaw,
        gnewsRaw,
        newsdataRaw,
        mediastackRaw,
        masterData
      ] = await Promise.all([
        fetchJson("/api/articles/newsapi"),
        fetchJson("/api/articles/gnews"),
        fetchJson("/api/raw/newsapi/latest"),
        fetchJson("/api/raw/gnews/latest"),
        fetchJson("/api/raw/secondary/newsdata"),
        fetchJson("/api/raw/secondary/mediastack"),
        fetchJson("/api/articles/master"),
      ]);

      newsapiRows = newsapiData.articles || [];
      gnewsRows = gnewsData.articles || [];
      masterRows = masterData.articles || [];
      renderTables();

      document.querySelector("#newsapiRawFile").textContent = newsapiRaw.filename || "n/a";
      document.querySelector("#gnewsRawFile").textContent = gnewsRaw.filename || "n/a";
      document.querySelector("#newsdataFile").textContent = newsdataRaw.filename || "n/a";
      document.querySelector("#mediastackFile").textContent = mediastackRaw.filename || "n/a";
      document.querySelector("#newsapiRaw").textContent = truncateJson(newsapiRaw.data);
      document.querySelector("#gnewsRaw").textContent = truncateJson(gnewsRaw.data);
      document.querySelector("#newsdataRaw").textContent = truncateJson(newsdataRaw.data);
      document.querySelector("#mediastackRaw").textContent = truncateJson(mediastackRaw.data);
    }

    document.querySelector("#refreshBtn").addEventListener("click", loadAll);
    searchInput.addEventListener("input", renderTables);
    loadAll();
  </script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, status: int, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/":
            self._send_html(200, build_html())
            return
        if path == "/api/health":
            self._send_json(200, {"status": "ok"})
            return
        if path == "/api/articles/newsapi":
            rows = read_csv_rows(NEWSAPI_CSV_PATH)
            self._send_json(200, {"count": len(rows), "articles": rows})
            return
        if path == "/api/articles/gnews":
            rows = read_csv_rows(GNEWS_CSV_PATH)
            self._send_json(200, {"count": len(rows), "articles": rows})
            return
        if path == "/api/articles/master":
            rows = read_csv_rows(MASTER_CSV_PATH)
            self._send_json(200, {"count": len(rows), "articles": rows})
            return
        if path == "/api/raw/newsapi/latest":
            self._send_json(200, read_latest_json(RAW_NEWSAPI_DIR))
            return
        if path == "/api/raw/gnews/latest":
            self._send_json(200, read_latest_json(RAW_GNEWS_DIR))
            return
        if path == "/api/raw/secondary/newsdata":
            p = SECONDARY_DIR / "newsdata_sample_response.json"
            self._send_json(200, read_json_file(p))
            return
        if path == "/api/raw/secondary/mediastack":
            p = SECONDARY_DIR / "mediastack_sample_response.json"
            self._send_json(200, read_json_file(p))
            return
        self._send_json(404, {"error": "Not found"})

    def log_message(self, format: str, *args) -> None:
        # Keep terminal output clean while serving local requests.
        return


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve multi-source local news portal.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=3000, help="Bind port")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Portal running at http://{args.host}:{args.port}")
    print(f"Reading CSV from: {NEWSAPI_CSV_PATH}")
    print(f"Reading CSV from: {GNEWS_CSV_PATH}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
