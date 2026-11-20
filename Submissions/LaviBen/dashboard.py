"""Build a self-contained interactive dashboard from saved benchmark JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>LaviBen saved-results dashboard</title>
  <style>
    :root {
      color-scheme: light;
      --ink: #172033;
      --muted: #64748b;
      --panel: #ffffff;
      --line: #dbe3ee;
      --accent: #2563eb;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: #f1f5f9;
      color: var(--ink);
      font: 15px/1.5 system-ui, sans-serif;
    }
    main { width: min(1440px, calc(100% - 32px)); margin: 30px auto 56px; }
    h1 { margin: 0; font-size: clamp(28px, 4vw, 44px); letter-spacing: -.03em; }
    h2 { margin: 0 0 12px; font-size: 20px; }
    h3 { margin: 0; font-size: 17px; }
    .subtitle, .note { color: var(--muted); }
    .panel, .chart-card, .stat, .controls {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 16px;
      box-shadow: 0 8px 24px #0f172a0d;
    }
    .panel { margin-top: 18px; padding: 20px; overflow: auto; }
    .controls {
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      align-items: end;
      margin: 20px 0 16px;
      padding: 16px;
    }
    label { display: grid; gap: 5px; color: var(--muted); font-size: 12px; }
    select, button {
      min-height: 38px;
      border: 1px solid #cbd5e1;
      border-radius: 9px;
      background: #fff;
      color: var(--ink);
      padding: 7px 10px;
      font: inherit;
    }
    button { cursor: pointer; color: #fff; background: var(--accent); border: 0; }
    .chips { display: flex; flex-wrap: wrap; gap: 8px; margin-left: auto; }
    .chip { background: #eaf1ff; color: #1e40af; border-radius: 999px; padding: 7px 10px; }
    .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; }
    .stat { padding: 16px; }
    .stat span { display: block; color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: .07em; }
    .stat b { display: block; margin-top: 4px; font-size: 22px; }
    .legend { display: flex; flex-wrap: wrap; gap: 10px 18px; margin: 10px 0 16px; }
    .legend span { display: inline-flex; align-items: center; gap: 7px; }
    .legend i { width: 11px; height: 11px; border-radius: 50%; }
    .chart-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(430px, 1fr)); gap: 14px; }
    .chart-card { padding: 14px; overflow: auto; }
    .chart-card p { margin: 3px 0 8px; color: var(--muted); font-size: 12px; }
    svg { display: block; width: 100%; min-width: 430px; }
    .grid-line { stroke: #dbe3ee; stroke-width: 1; }
    .axis-label { fill: #64748b; font-size: 11px; }
    .axis-title { fill: #334155; font-size: 12px; font-weight: 600; }
    table { width: 100%; border-collapse: collapse; white-space: nowrap; }
    th, td { padding: 9px 10px; border-bottom: 1px solid #e2e8f0; text-align: right; }
    th { color: #475569; font-size: 11px; text-transform: uppercase; letter-spacing: .04em; }
    th:first-child, td:first-child, .text-left { text-align: left; }
    details { margin-top: 18px; }
    summary { cursor: pointer; font-weight: 650; }
    pre { overflow: auto; padding: 14px; border-radius: 12px; background: #0f172a; color: #dbeafe; }
    code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
    .raw-wrap { max-height: 500px; overflow: auto; margin-top: 12px; }
    @media (max-width: 680px) { .chips { margin-left: 0; } }
  </style>
</head>
<body>
<main>
  <h1>Search runtime dashboard</h1>
  <p class="subtitle">
    Interactive views over saved measurements. Changing a control filters the
    embedded results and never reruns a benchmark.
  </p>

  <section class="controls" aria-label="Dashboard filters">
    <label>Query count
      <select id="query-count"></select>
    </label>
    <label>Query scenario
      <select id="scenario"></select>
    </label>
    <button id="download-raw" type="button">Download selected raw repeats</button>
    <div class="chips">
      <span class="chip" id="hit-rate"></span>
      <span class="chip" id="time-units"></span>
      <span class="chip" id="memory-units"></span>
    </div>
  </section>

  <section class="stats">
    <article class="stat"><span>Selected fixed cases</span><b id="case-count"></b></article>
    <article class="stat"><span>Selected raw repeats</span><b id="raw-count"></b></article>
    <article class="stat"><span>Selected memory runs</span><b id="memory-count"></b></article>
    <article class="stat"><span>Largest input length</span><b id="largest-input"></b></article>
  </section>

  <section class="panel">
    <h2>Elapsed time against input length</h2>
    <div class="legend" id="legend"></div>
    <div class="chart-grid">
      <article class="chart-card">
        <h3>Preparation time</h3><p>Median milliseconds, logarithmic y-axis</p>
        <svg id="chart-preparation" viewBox="0 0 640 330"></svg>
      </article>
      <article class="chart-card">
        <h3>Query-batch time</h3><p>Complete ordered batch; median milliseconds</p>
        <svg id="chart-query" viewBox="0 0 640 330"></svg>
      </article>
      <article class="chart-card">
        <h3>Total time</h3><p>Preparation plus complete batch; median milliseconds</p>
        <svg id="chart-total" viewBox="0 0 640 330"></svg>
      </article>
    </div>
  </section>

  <section class="panel">
    <h2>Original vs revised binary search</h2>
    <p class="note">Recursive v1 and iterative v2 on the same saved inputs.</p>
    <table>
      <thead><tr><th>Input length</th><th class="text-left">Version</th>
        <th>Preparation median (ms)</th><th>Query median (ms)</th>
        <th>Total median (ms)</th></tr></thead>
      <tbody id="version-comparison"></tbody>
    </table>
  </section>

  <section class="panel">
    <h2>Chosen memory measurements</h2>
    <p class="note">
      Peak traced memory uses a fresh <code>tracemalloc</code> run per method.
      Input is excluded; preparation and output are included.
    </p>
    <table>
      <thead><tr><th>Input length</th><th class="text-left">Method</th>
        <th>Current traced bytes</th><th>Peak traced memory (bytes)</th>
        <th>Peak KiB</th></tr></thead>
      <tbody id="memory-table"></tbody>
    </table>
  </section>

  <section class="panel">
    <h2>Saved-data access</h2>
    <p class="note">
      Source: <code>results/benchmark_results.json</code>. The generator embeds
      that file in this portable HTML; browser view changes only filter it.
    </p>
    <details>
      <summary>Raw repeats</summary>
      <div class="raw-wrap">
        <table><thead><tr><th>Input</th><th class="text-left">Method</th>
          <th>Repeat</th><th>Order</th><th>Preparation ns</th>
          <th>Query ns</th><th>Total ns</th><th>Input SHA-256</th></tr></thead>
          <tbody id="raw-table"></tbody>
        </table>
      </div>
    </details>
    <details>
      <summary>Environment details</summary>
      <pre id="environment-details"></pre>
    </details>
  </section>
</main>

<script>
const benchmarkData = __BENCHMARK_DATA__;
const colors = ["#2563eb", "#9333ea", "#ea580c", "#059669"];
const summaryRows = benchmarkData.summary;
const caseRows = benchmarkData.cases;
const rawRows = benchmarkData.raw_results;
const memoryRows = benchmarkData.memory_results;
const metadata = benchmarkData.metadata;
const algorithms = [...new Set(summaryRows.map(row => row.algorithm))];
const caseById = new Map(caseRows.map(row => [row.case_id, row]));

const querySelect = document.getElementById("query-count");
const scenarioSelect = document.getElementById("scenario");

function uniqueSorted(values, numeric = false) {
  const valuesUnique = [...new Set(values)];
  return valuesUnique.sort(numeric ? ((a, b) => Number(a) - Number(b)) : undefined);
}

function addOptions(select, values) {
  select.innerHTML = values.map(value =>
    `<option value="${String(value)}">${String(value)}</option>`
  ).join("");
}

addOptions(querySelect, uniqueSorted(summaryRows.map(row => row.query_count), true));
addOptions(scenarioSelect, uniqueSorted(summaryRows.map(row => row.scenario)));
querySelect.value = String(Math.max(...summaryRows.map(row => Number(row.query_count))));
if ([...scenarioSelect.options].some(option => option.value === "mixed")) {
  scenarioSelect.value = "mixed";
}

function selectedQueryCount() { return Number(querySelect.value); }
function selectedScenario() { return scenarioSelect.value; }
function formatNumber(value, digits = 6) {
  return Number(value).toLocaleString(undefined, { maximumFractionDigits: digits });
}
function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, character => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[character]);
}

function filteredSummary() {
  return summaryRows.filter(row =>
    Number(row.query_count) === selectedQueryCount() &&
    row.scenario === selectedScenario()
  );
}
function filteredCases() {
  return caseRows.filter(row =>
    Number(row.query_count) === selectedQueryCount() &&
    row.scenario === selectedScenario()
  );
}
function filteredRaw() {
  const selectedCaseIds = new Set(filteredCases().map(row => row.case_id));
  return rawRows.filter(row => selectedCaseIds.has(row.case_id));
}
function filteredMemory() {
  return memoryRows.filter(row =>
    Number(row.query_count) === selectedQueryCount() &&
    row.scenario === selectedScenario()
  );
}

function renderLegend() {
  document.getElementById("legend").innerHTML = algorithms.map((algorithm, index) =>
    `<span><i style="background:${colors[index % colors.length]}"></i>${escapeHtml(algorithm)}</span>`
  ).join("");
}

function renderChart(svgId, metric) {
  const svg = document.getElementById(svgId);
  const rows = filteredSummary();
  const sizes = uniqueSorted(rows.map(row => Number(row.array_size)), true);
  const width = 640, height = 330, left = 72, right = 20, top = 20, bottom = 58;
  const chartWidth = width - left - right;
  const chartHeight = height - top - bottom;
  const values = rows.map(row => Math.max(Number(row[metric]), 1e-9));
  let logMin = Math.log10(Math.min(...values));
  let logMax = Math.log10(Math.max(...values));
  if (Math.abs(logMax - logMin) < 1e-12) { logMin -= .5; logMax += .5; }
  const x = index => sizes.length === 1
    ? left + chartWidth / 2
    : left + index * chartWidth / (sizes.length - 1);
  const y = value => top + chartHeight *
    (1 - (Math.log10(Math.max(value, 1e-9)) - logMin) / (logMax - logMin));
  const parts = [];
  for (let index = 0; index < 5; index += 1) {
    const proportion = index / 4;
    const value = 10 ** (logMin + (logMax - logMin) * proportion);
    const yPosition = top + chartHeight * (1 - proportion);
    parts.push(`<line x1="${left}" y1="${yPosition}" x2="${width - right}" y2="${yPosition}" class="grid-line"/>`);
    parts.push(`<text x="${left - 8}" y="${yPosition + 4}" text-anchor="end" class="axis-label">${formatNumber(value)}</text>`);
  }
  sizes.forEach((size, index) => {
    parts.push(`<text x="${x(index)}" y="${height - 30}" text-anchor="middle" class="axis-label">${size.toLocaleString()}</text>`);
  });
  algorithms.forEach((algorithm, algorithmIndex) => {
    const series = sizes.map((size, index) => {
      const row = rows.find(item => item.algorithm === algorithm && Number(item.array_size) === size);
      return { x: x(index), y: y(Number(row[metric])), row };
    });
    const points = series.map(point => `${point.x},${point.y}`).join(" ");
    const color = colors[algorithmIndex % colors.length];
    parts.push(`<polyline points="${points}" fill="none" stroke="${color}" stroke-width="3" stroke-linejoin="round"/>`);
    series.forEach(point => parts.push(
      `<circle cx="${point.x}" cy="${point.y}" r="4" fill="${color}"><title>${escapeHtml(algorithm)} · n=${Number(point.row.array_size).toLocaleString()} · ${formatNumber(point.row[metric])} ms</title></circle>`
    ));
  });
  parts.push(`<text x="${left + chartWidth / 2}" y="${height - 4}" text-anchor="middle" class="axis-title">Input length (n)</text>`);
  parts.push(`<text x="15" y="${top + chartHeight / 2}" text-anchor="middle" class="axis-title" transform="rotate(-90 15 ${top + chartHeight / 2})">Median ms (log scale)</text>`);
  svg.innerHTML = parts.join("");
}

function renderHeader() {
  const cases = filteredCases();
  const raw = filteredRaw();
  const memory = filteredMemory();
  const requested = uniqueSorted(cases.map(row => Number(row.requested_hit_rate)));
  const realized = uniqueSorted(cases.map(row => Number(row.realized_hit_rate)));
  document.getElementById("case-count").textContent = cases.length.toLocaleString();
  document.getElementById("raw-count").textContent = raw.length.toLocaleString();
  document.getElementById("memory-count").textContent = memory.length.toLocaleString();
  document.getElementById("largest-input").textContent =
    Math.max(...cases.map(row => Number(row.array_size))).toLocaleString();
  document.getElementById("hit-rate").textContent =
    `Hit rate requested ${requested.join("–")}; realized ${realized.join("–")}`;
  document.getElementById("time-units").textContent =
    `Time: ${metadata.units.summary_timings} summary / ${metadata.units.raw_timings} raw`;
  document.getElementById("memory-units").textContent =
    `Memory: ${metadata.units.traced_memory}`;
}

function renderVersionComparison() {
  const rows = filteredSummary().filter(row => row.algorithm.includes("Binary search"));
  rows.sort((a, b) => Number(a.array_size) - Number(b.array_size) ||
    a.algorithm.localeCompare(b.algorithm));
  document.getElementById("version-comparison").innerHTML = rows.map(row =>
    `<tr><td>${Number(row.array_size).toLocaleString()}</td>` +
    `<td class="text-left">${escapeHtml(row.algorithm)}</td>` +
    `<td>${formatNumber(row.preparation_median_ms)}</td>` +
    `<td>${formatNumber(row.query_batch_median_ms)}</td>` +
    `<td>${formatNumber(row.combined_median_ms)}</td></tr>`
  ).join("");
}

function renderMemory() {
  const rows = filteredMemory().sort((a, b) =>
    Number(a.array_size) - Number(b.array_size) || a.algorithm.localeCompare(b.algorithm));
  document.getElementById("memory-table").innerHTML = rows.map(row =>
    `<tr><td>${Number(row.array_size).toLocaleString()}</td>` +
    `<td class="text-left">${escapeHtml(row.algorithm)}</td>` +
    `<td>${Number(row.current_traced_bytes).toLocaleString()}</td>` +
    `<td>${Number(row.peak_traced_bytes).toLocaleString()}</td>` +
    `<td>${formatNumber(Number(row.peak_traced_bytes) / 1024, 2)}</td></tr>`
  ).join("");
}

function renderRaw() {
  const rows = filteredRaw().sort((a, b) => {
    const caseA = caseById.get(a.case_id), caseB = caseById.get(b.case_id);
    return Number(caseA.array_size) - Number(caseB.array_size) ||
      a.algorithm.localeCompare(b.algorithm) || Number(a.repeat) - Number(b.repeat);
  });
  document.getElementById("raw-table").innerHTML = rows.map(row => {
    const benchmarkCase = caseById.get(row.case_id);
    return `<tr><td>${Number(benchmarkCase.array_size).toLocaleString()}</td>` +
      `<td class="text-left">${escapeHtml(row.algorithm)}</td>` +
      `<td>${row.repeat}</td><td>${row.order_position}</td>` +
      `<td>${Number(row.preparation_ns).toLocaleString()}</td>` +
      `<td>${Number(row.query_batch_ns).toLocaleString()}</td>` +
      `<td>${Number(row.combined_ns).toLocaleString()}</td>` +
      `<td><code>${escapeHtml(row.input_sha256.slice(0, 12))}…</code></td></tr>`;
  }).join("");
}

function renderEnvironment() {
  const details = {
    units: metadata.units,
    environment: metadata.environment,
    code_version: metadata.code_version,
    benchmark_settings: metadata.benchmark_settings,
    generator_settings: metadata.generator_settings,
    memory_settings: metadata.memory_settings
  };
  document.getElementById("environment-details").textContent =
    JSON.stringify(details, null, 2);
}

function downloadRaw() {
  const rows = filteredRaw();
  const columns = ["case_id", "algorithm", "version", "repeat", "order_position",
    "input_sha256", "preparation_ns", "query_batch_ns", "combined_ns"];
  const quote = value => `"${String(value).replaceAll('"', '""')}"`;
  const csv = [columns.join(","), ...rows.map(row =>
    columns.map(column => quote(row[column])).join(",")
  )].join("\n");
  const link = document.createElement("a");
  link.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
  link.download = `raw-q${selectedQueryCount()}-${selectedScenario()}.csv`;
  link.click();
  URL.revokeObjectURL(link.href);
}

function renderAll() {
  renderHeader();
  renderChart("chart-preparation", "preparation_median_ms");
  renderChart("chart-query", "query_batch_median_ms");
  renderChart("chart-total", "combined_median_ms");
  renderVersionComparison();
  renderMemory();
  renderRaw();
}

querySelect.addEventListener("change", renderAll);
scenarioSelect.addEventListener("change", renderAll);
document.getElementById("download-raw").addEventListener("click", downloadRaw);
renderLegend();
renderEnvironment();
renderAll();
</script>
</body>
</html>
"""


def build_dashboard(results_path: Path, output_path: Path) -> Path:
    """Embed saved measurements in an interactive, dependency-free HTML app."""

    payload = json.loads(results_path.read_text(encoding="utf-8"))
    required_sections = (
        "metadata",
        "cases",
        "raw_results",
        "summary",
        "memory_results",
    )
    missing = [section for section in required_sections if not payload.get(section)]
    if missing:
        raise ValueError(f"benchmark JSON is missing data: {', '.join(missing)}")

    embedded_json = json.dumps(payload, separators=(",", ":")).replace(
        "</",
        "<\\/",
    )
    document = HTML_TEMPLATE.replace("__BENCHMARK_DATA__", embedded_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(document, encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("results/benchmark_results.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/runtime_dashboard.html"),
    )
    arguments = parser.parse_args()
    output_path = build_dashboard(arguments.input, arguments.output)
    print(f"Wrote {output_path} from saved results only")


if __name__ == "__main__":
    main()
