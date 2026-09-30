#!/usr/bin/env python3
"""Create an editable HTML table for a wordlist CSV."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

import pandas as pd


def _build_html(rows_json: str, source_csv_name: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Wordlist Keep Editor</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      margin: 16px;
      color: #222;
    }}
    .toolbar {{
      display: flex;
      gap: 12px;
      align-items: center;
      margin-bottom: 12px;
      flex-wrap: wrap;
    }}
    button {{
      border: 1px solid #888;
      background: #f5f5f5;
      padding: 6px 10px;
      border-radius: 4px;
      cursor: pointer;
    }}
    button:hover {{
      background: #ebebeb;
    }}
    .toggle-yes {{
      background: #e8f5e9;
      border-color: #66bb6a;
    }}
    .toggle-no {{
      background: #ffebee;
      border-color: #ef5350;
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
    }}
    th, td {{
      border: 1px solid #ddd;
      padding: 6px 8px;
      text-align: left;
    }}
    th {{
      position: sticky;
      top: 0;
      background: #fafafa;
      z-index: 1;
    }}
    td.count {{
      text-align: right;
      width: 90px;
    }}
    .table-wrap {{
      max-height: 45vh;
      overflow: auto;
      border: 1px solid #ddd;
      margin-bottom: 16px;
    }}
    .meta {{
      color: #555;
      font-size: 0.95rem;
    }}
    .section-title {{
      margin: 8px 0 6px;
      font-size: 1rem;
    }}
  </style>
</head>
<body>
  <h2>Wordlist Keep Editor</h2>
  <div class="meta">Source CSV: <code>{source_csv_name}</code></div>
  <div class="toolbar">
    <button id="downloadCsvBtn">Download Updated CSV</button>
    <button id="saveHtmlBtn">Save HTML</button>
    <button id="markAllKeepYesBtn">Set All Visible Keep=Yes</button>
    <button id="markAllKeepNoBtn">Set All Visible Keep=No</button>
    <label>
      Filter term:
      <input id="termFilter" type="text" placeholder="type to filter..." />
    </label>
    <span id="countsLabel"></span>
  </div>

  <div class="section-title"><strong>Kept</strong></div>
  <div class="table-wrap">
    <table id="keptTable">
      <thead>
        <tr>
          <th>term</th>
          <th>count</th>
          <th>Keep</th>
        </tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>

  <div class="section-title"><strong>Rejected</strong></div>
  <div class="table-wrap">
    <table id="rejectedTable">
      <thead>
        <tr>
          <th>term</th>
          <th>count</th>
          <th>Keep</th>
        </tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>

<script id="rows-data" type="application/json">{rows_json}</script>
<script>
const rows = JSON.parse(document.getElementById("rows-data").textContent);

function normalizeFlag(value) {{
  return String(value).trim().toLowerCase() === "no" ? "No" : "Yes";
}}

function escapeCsv(value) {{
  const text = String(value ?? "");
  if (text.includes(",") || text.includes('"') || text.includes("\\n")) {{
    return '"' + text.replaceAll('"', '""') + '"';
  }}
  return text;
}}

function setButtonStyle(button, value) {{
  button.textContent = value;
  button.className = value === "Yes" ? "toggle-yes" : "toggle-no";
}}

function updateCounts() {{
  const keptCount = rows.filter(r => r.Keep === "Yes").length;
  const rejectedCount = rows.filter(r => r.Keep === "No").length;
  const total = rows.length;
  document.getElementById("countsLabel").textContent = `Kept: ${{keptCount}} / Rejected: ${{rejectedCount}} / Total: ${{total}}`;
}}

function createRowElement(row) {{
  const tr = document.createElement("tr");
  const termTd = document.createElement("td");
  termTd.textContent = row.term;
  tr.appendChild(termTd);

  const countTd = document.createElement("td");
  countTd.className = "count";
  countTd.textContent = row.count;
  tr.appendChild(countTd);

  const toggleTd = document.createElement("td");
  const toggleBtn = document.createElement("button");
  setButtonStyle(toggleBtn, row.Keep);
  toggleBtn.addEventListener("click", () => {{
    row.Keep = row.Keep === "Yes" ? "No" : "Yes";
    renderTables();
  }});
  toggleTd.appendChild(toggleBtn);
  tr.appendChild(toggleTd);
  return tr;
}}

function renderTables() {{
  const keptBody = document.querySelector("#keptTable tbody");
  const rejectedBody = document.querySelector("#rejectedTable tbody");
  const filter = document.getElementById("termFilter").value.trim().toLowerCase();
  keptBody.innerHTML = "";
  rejectedBody.innerHTML = "";
  rows.forEach((row) => {{
    if (filter && !String(row.term).toLowerCase().includes(filter)) {{
      return;
    }}
    const tr = createRowElement(row);
    if (row.Keep === "Yes") {{
      keptBody.appendChild(tr);
    }} else {{
      rejectedBody.appendChild(tr);
    }}
  }});
  updateCounts();
}}

function downloadCsv() {{
  const header = ["term", "count", "Keep"];
  const lines = [header.join(",")];
  rows.forEach((row) => {{
    lines.push([
      escapeCsv(row.term),
      escapeCsv(row.count),
      escapeCsv(row.Keep)
    ].join(","));
  }});
  const csvContent = lines.join("\\n");
  const blob = new Blob([csvContent], {{ type: "text/csv;charset=utf-8;" }});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "raw_wordlist_keep.csv";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}}

function saveHtml() {{
  document.getElementById("rows-data").textContent = JSON.stringify(rows);
  const html = "<!DOCTYPE html>\\n" + document.documentElement.outerHTML;
  const blob = new Blob([html], {{ type: "text/html;charset=utf-8;" }});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "raw_wordlist_editor_saved.html";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}}

function setVisibleRowsKeep(value) {{
  const filter = document.getElementById("termFilter").value.trim().toLowerCase();
  rows.forEach((row) => {{
    if (filter && !String(row.term).toLowerCase().includes(filter)) {{
      return;
    }}
    row.Keep = value;
  }});
  renderTables();
}}

rows.forEach((row) => {{
  row.Keep = normalizeFlag(row.Keep);
}});

document.getElementById("downloadCsvBtn").addEventListener("click", downloadCsv);
document.getElementById("saveHtmlBtn").addEventListener("click", saveHtml);
document.getElementById("markAllKeepYesBtn").addEventListener("click", () => setVisibleRowsKeep("Yes"));
document.getElementById("markAllKeepNoBtn").addEventListener("click", () => setVisibleRowsKeep("No"));
document.getElementById("termFilter").addEventListener("input", renderTables);
renderTables();
</script>
</body>
</html>
"""


def _load_rows(df: pd.DataFrame) -> List[Dict[str, object]]:
    if "Keep" in df.columns:
        rows_df = df[["term", "count", "Keep"]].copy()
        rows_df["Keep"] = rows_df["Keep"].apply(
            lambda value: "No" if str(value).strip().lower() == "no" else "Yes"
        )
        return rows_df.to_dict(orient="records")

    if "manual_delete" in df.columns:
        rows_df = df[["term", "count", "manual_delete"]].copy()
        rows_df["Keep"] = rows_df["manual_delete"].apply(
            lambda value: "No" if str(value).strip().lower() == "yes" else "Yes"
        )
        rows_df = rows_df[["term", "count", "Keep"]]
        return rows_df.to_dict(orient="records")

    raise ValueError("Input CSV must contain either 'Keep' or 'manual_delete' column")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create editable HTML wordlist table with Keep toggles"
    )
    parser.add_argument("--input-csv", required=True, help="Wordlist CSV file")
    parser.add_argument(
        "--output-html",
        default=None,
        help="Output HTML path (default: <input_stem>_editor.html)",
    )
    args = parser.parse_args()

    input_csv = Path(args.input_csv).resolve()
    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    df = pd.read_csv(input_csv)
    if "term" not in df.columns or "count" not in df.columns:
        raise ValueError("Input CSV must contain 'term' and 'count' columns")

    rows = _load_rows(df=df)
    rows_json = json.dumps(rows, ensure_ascii=True)

    output_html = (
        Path(args.output_html).resolve()
        if args.output_html
        else Path(input_csv.parent, f"{input_csv.stem}_editor.html")
    )
    output_html.write_text(
        _build_html(rows_json=rows_json, source_csv_name=input_csv.name),
        encoding="utf-8",
    )
    print(f"Created editor HTML: {output_html}")


if __name__ == "__main__":
    main()
