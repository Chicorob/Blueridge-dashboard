import re, os, sys

inpath = r"C:\Users\RobSchulz\OneDrive - Suttons Creek, Inc\Desktop\BlueRidge Life Sciences Dashboardv2_6.html"
outpath = r"C:\Users\RobSchulz\OneDrive - Suttons Creek, Inc\Desktop\BlueRidge Life Sciences Dashboardv2_7.html"

with open(inpath, "r", encoding="utf-8") as f:
    html = f.read()

# ============================================================
# 1. Add "Corporate Services" division
# ============================================================

html = html.replace(
    'DIVISIONS: ["Clintrex", "ToxStrategies", "Suttons Creek", "Modality", "Design Science"],',
    'DIVISIONS: ["Clintrex", "ToxStrategies", "Suttons Creek", "Modality", "Design Science", "Corporate Services"],'
)

html = html.replace(
    '"Design Science": "#5DAE3B", "BlueRidge Life Sciences": "#1A1A2E"',
    '"Design Science": "#5DAE3B", "Corporate Services": "#8E44AD", "BlueRidge Life Sciences": "#1A1A2E"'
)

html = html.replace(
    '"Design Science": { "Pipeline":12e6,"Weighted Pipeline":6.5e6,"Closed Sales":5e6,"Win Rate":44,"Revenue":10e6,"EBITDA":2.2e6,"Cash Collections":9.2e6,"Utilization":74,"Headcount":60,"Backlog":11e6,"FTE":54 }',
    '"Design Science": { "Pipeline":12e6,"Weighted Pipeline":6.5e6,"Closed Sales":5e6,"Win Rate":44,"Revenue":10e6,"EBITDA":2.2e6,"Cash Collections":9.2e6,"Utilization":74,"Headcount":60,"Backlog":11e6,"FTE":54 },\n    "Corporate Services": { "Pipeline":8e6,"Weighted Pipeline":4e6,"Closed Sales":3.2e6,"Win Rate":36,"Revenue":6.5e6,"EBITDA":1.4e6,"Cash Collections":6e6,"Utilization":65,"Headcount":35,"Backlog":7e6,"FTE":30 }'
)

html = html.replace(
    '<option>Design Science</option>\n      </select>',
    '<option>Design Science</option>\n        <option>Corporate Services</option>\n      </select>'
)

# ============================================================
# 2. Time range labels with specific date context
# ============================================================

html = html.replace(
    '<select id="timeRange">\n        <option>Month</option>\n        <option selected="">Quarter</option>\n        <option>Current Year</option>\n        <option>Trailing 12 Months</option>\n        <option>Custom Range</option>\n      </select>',
    '<select id="timeRange">\n        <option value="Month">Month</option>\n        <option value="Quarter" selected="">Quarter</option>\n        <option value="Current Year">Current Year</option>\n        <option value="Trailing 12 Months">Trailing 12 Months</option>\n        <option value="Custom Range">Custom Range</option>\n      </select>'
)

time_label_fn = """// ==================== TIME RANGE LABELS ====================
function updateTimeRangeLabels() {
  if (!dashboardData) return;
  var last = dashboardData.dates[dashboardData.dates.length - 1];
  var monthNames = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  var mon = monthNames[last.getMonth()];
  var yr = last.getFullYear();
  var qtr = "Q" + (Math.floor(last.getMonth() / 3) + 1);
  var sel = document.getElementById("timeRange");
  if (!sel) return;
  for (var oi = 0; oi < sel.options.length; oi++) {
    var opt = sel.options[oi];
    if (opt.value === "Month") opt.textContent = "Month (" + mon + " " + yr + ")";
    else if (opt.value === "Quarter") opt.textContent = "Quarter (" + qtr + " " + yr + ")";
    else if (opt.value === "Current Year") opt.textContent = "Current Year (" + yr + ")";
    else if (opt.value === "Trailing 12 Months") opt.textContent = "Trailing 12 Months";
    else if (opt.value === "Custom Range") opt.textContent = "Custom Range";
  }
}

"""

html = html.replace(
    "// ==================== INIT ====================",
    time_label_fn + "// ==================== INIT ===================="
)

html = html.replace(
    'generateData();\nnavigateTo("executive");',
    'generateData();\nupdateTimeRangeLabels();\nnavigateTo("executive");'
)

# ============================================================
# 3. Add Revenue/FTE and EBITDA/FTE KPIs + Utilization avg
# ============================================================

old_getKPIs = """function getKPIs(entity, timeRange) {
  const data = getEntityData(entity);
  const currIdx = filterByTimeRange(timeRange);
  const priorIdx = getPriorPeriodIndices(timeRange);
  return CONFIG.METRICS.map(metric => {
    const current = aggregateForPeriod(data, metric, currIdx);
    const prior = aggregateForPeriod(data, metric, priorIdx);
    const delta = computeDelta(current, prior);
    return { metric, current, prior, delta, source: CONFIG.DATA_SOURCES[metric] };
  });
}"""

new_getKPIs = """function getKPIs(entity, timeRange) {
  const data = getEntityData(entity);
  const currIdx = filterByTimeRange(timeRange);
  const priorIdx = getPriorPeriodIndices(timeRange);
  const kpis = CONFIG.METRICS.map(metric => {
    let current = aggregateForPeriod(data, metric, currIdx);
    let prior = aggregateForPeriod(data, metric, priorIdx);
    // Utilization: show average over time range unless Month is selected
    if (metric === "Utilization" && timeRange !== "Month") {
      const currVals = currIdx.map(i => data[metric][i]);
      current = currVals.length ? currVals.reduce((a, b) => a + b, 0) / currVals.length : 0;
      const priorVals = priorIdx.map(i => data[metric][i]);
      prior = priorVals.length ? priorVals.reduce((a, b) => a + b, 0) / priorVals.length : 0;
    }
    const delta = computeDelta(current, prior);
    return { metric, current, prior, delta, source: CONFIG.DATA_SOURCES[metric] };
  });
  // Add computed KPIs: Revenue / FTE and EBITDA / FTE
  const revKPI = kpis.find(k => k.metric === "Revenue");
  const ebitdaKPI = kpis.find(k => k.metric === "EBITDA");
  const fteKPI = kpis.find(k => k.metric === "FTE");
  if (revKPI && fteKPI && fteKPI.current > 0) {
    const currRevFTE = revKPI.current / fteKPI.current;
    const priorRevFTE = (fteKPI.prior > 0) ? revKPI.prior / fteKPI.prior : 0;
    kpis.push({ metric: "Revenue / FTE", current: currRevFTE, prior: priorRevFTE, delta: computeDelta(currRevFTE, priorRevFTE), source: "Calculated" });
  }
  if (ebitdaKPI && fteKPI && fteKPI.current > 0) {
    const currEbFTE = ebitdaKPI.current / fteKPI.current;
    const priorEbFTE = (fteKPI.prior > 0) ? ebitdaKPI.prior / fteKPI.prior : 0;
    kpis.push({ metric: "EBITDA / FTE", current: currEbFTE, prior: priorEbFTE, delta: computeDelta(currEbFTE, priorEbFTE), source: "Calculated" });
  }
  return kpis;
}"""

html = html.replace(old_getKPIs, new_getKPIs)

# Update formatValue for Revenue/FTE and EBITDA/FTE
old_formatValue = """function formatValue(val, metric) {
  if (metric === "FTE") return val.toFixed(1);
  if (CONFIG.COUNT_METRICS.includes(metric)) return Math.round(val).toLocaleString();
  if (CONFIG.PERCENT_METRICS.includes(metric)) return val.toFixed(1) + "%";
  if (Math.abs(val) >= 1e6) return "$" + (val / 1e6).toFixed(1) + "M";
  if (Math.abs(val) >= 1e3) return "$" + Math.round(val / 1e3).toLocaleString() + "K";
  return "$" + Math.round(val).toLocaleString();
}"""

new_formatValue = """function formatValue(val, metric) {
  if (metric === "FTE") return val.toFixed(1);
  if (CONFIG.COUNT_METRICS.includes(metric)) return Math.round(val).toLocaleString();
  if (CONFIG.PERCENT_METRICS.includes(metric)) return val.toFixed(1) + "%";
  if (metric === "Revenue / FTE" || metric === "EBITDA / FTE") {
    if (Math.abs(val) >= 1e6) return "$" + (val / 1e6).toFixed(1) + "M";
    if (Math.abs(val) >= 1e3) return "$" + (val / 1e3).toFixed(1) + "K";
    return "$" + Math.round(val).toLocaleString();
  }
  if (Math.abs(val) >= 1e6) return "$" + (val / 1e6).toFixed(1) + "M";
  if (Math.abs(val) >= 1e3) return "$" + Math.round(val / 1e3).toLocaleString() + "K";
  return "$" + Math.round(val).toLocaleString();
}"""

html = html.replace(old_formatValue, new_formatValue)

# Update KPI card layout for dynamic rows of 4
old_renderKPI = """function renderKPICards(container, entity, timeRange) {
  const kpis = getKPIs(entity, timeRange);
  // Row 1: first 4, Row 2: next 4, Row 3: remaining
  let html = '<div class="kpi-row">';
  kpis.slice(0, 4).forEach(k => { html += kpiCardHTML(k); });
  html += '</div><div class="kpi-row">';
  kpis.slice(4, 8).forEach(k => { html += kpiCardHTML(k); });
  html += '</div><div class="kpi-row" style="grid-template-columns:repeat(' + Math.min(kpis.length - 8, 4) + ',1fr);">';
  kpis.slice(8).forEach(k => { html += kpiCardHTML(k); });
  html += '</div>';
  container.innerHTML = html;
}"""

new_renderKPI = """function renderKPICards(container, entity, timeRange) {
  const kpis = getKPIs(entity, timeRange);
  // Render in rows of 4
  let html = '';
  for (let r = 0; r < Math.ceil(kpis.length / 4); r++) {
    const rowKpis = kpis.slice(r * 4, r * 4 + 4);
    html += '<div class="kpi-row" style="grid-template-columns:repeat(' + rowKpis.length + ',1fr);">';
    rowKpis.forEach(k => { html += kpiCardHTML(k); });
    html += '</div>';
  }
  container.innerHTML = html;
}"""

html = html.replace(old_renderKPI, new_renderKPI)

# ============================================================
# 4. Remove BLS from Entity on Division Detail
# ============================================================

old_divDetail = """function renderDivisionDetail() {
  const el = document.getElementById("page-division");
  const entity = selectedEntity === CONFIG.COMPANY_NAME ? "Clintrex" : selectedEntity;"""

new_divDetail = """function renderDivisionDetail() {
  const el = document.getElementById("page-division");
  // Auto-select first division if BlueRidge is selected on Division Detail
  if (selectedEntity === CONFIG.COMPANY_NAME) {
    selectedEntity = CONFIG.DIVISIONS[0];
    document.getElementById("entitySelect").value = selectedEntity;
    document.getElementById("headerSub").textContent = selectedEntity + " | " + getTimeRangeLabel();
  }
  const entity = selectedEntity;"""

html = html.replace(old_divDetail, new_divDetail)

# Update navigateTo to show/hide BLS option
old_navigateTo = """function navigateTo(page) {
  currentPage = page;
  document.querySelectorAll(".nav-btn").forEach(b => b.classList.toggle("active", b.dataset.page === page));
  document.querySelectorAll(".page-content").forEach(p => p.classList.add("hidden"));
  document.getElementById("page-" + page).classList.remove("hidden");
  document.getElementById("headerTitle").textContent = pageNames[page];
  document.getElementById("headerSub").textContent = selectedEntity + " | " + getTimeRangeLabel();
  renderCurrentPage();
}"""

new_navigateTo = """function navigateTo(page) {
  currentPage = page;
  document.querySelectorAll(".nav-btn").forEach(b => b.classList.toggle("active", b.dataset.page === page));
  document.querySelectorAll(".page-content").forEach(p => p.classList.add("hidden"));
  document.getElementById("page-" + page).classList.remove("hidden");
  document.getElementById("headerTitle").textContent = pageNames[page];
  // Show/hide BlueRidge option in entity dropdown based on page
  var entitySel = document.getElementById("entitySelect");
  var blsOpt = null;
  for (var oi = 0; oi < entitySel.options.length; oi++) {
    if (entitySel.options[oi].textContent === "BlueRidge Life Sciences") { blsOpt = entitySel.options[oi]; break; }
  }
  if (blsOpt) {
    if (page === "division") {
      blsOpt.style.display = "none";
      blsOpt.disabled = true;
      if (selectedEntity === CONFIG.COMPANY_NAME) {
        selectedEntity = CONFIG.DIVISIONS[0];
        entitySel.value = selectedEntity;
      }
    } else {
      blsOpt.style.display = "";
      blsOpt.disabled = false;
    }
  }
  document.getElementById("headerSub").textContent = selectedEntity + " | " + getTimeRangeLabel();
  renderCurrentPage();
}"""

html = html.replace(old_navigateTo, new_navigateTo)

# ============================================================
# 5. Update getTimeRangeLabel with contextual date labels
# ============================================================

old_trLabel = """function getTimeRangeLabel() {
  if (selectedTimeRange === "Custom Range") {
    const s = document.getElementById("customStart");
    const e = document.getElementById("customEnd");
    if (s && e && s.value && e.value) return s.value + " to " + e.value;
    return "Custom Range";
  }
  return selectedTimeRange;
}"""

new_trLabel = """function getTimeRangeLabel() {
  if (selectedTimeRange === "Custom Range") {
    var s = document.getElementById("customStart");
    var e = document.getElementById("customEnd");
    if (s && e && s.value && e.value) return s.value + " to " + e.value;
    return "Custom Range";
  }
  if (dashboardData) {
    var last = dashboardData.dates[dashboardData.dates.length - 1];
    var monthNames = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
    var yr = last.getFullYear();
    if (selectedTimeRange === "Month") return "Month (" + monthNames[last.getMonth()] + " " + yr + ")";
    if (selectedTimeRange === "Quarter") return "Quarter (Q" + (Math.floor(last.getMonth() / 3) + 1) + " " + yr + ")";
    if (selectedTimeRange === "Current Year") return "Current Year (" + yr + ")";
  }
  return selectedTimeRange;
}"""

html = html.replace(old_trLabel, new_trLabel)

# Write
with open(outpath, "w", encoding="utf-8") as f:
    f.write(html)

size_mb = os.path.getsize(outpath) / (1024*1024)
print(f"Created: {outpath}")
print(f"Size: {size_mb:.1f} MB")

# Verify
checks = [
    ("Corporate Services in DIVISIONS", "Corporate Services" in html),
    ("Corporate Services profile", '"Corporate Services":' in html),
    ("Corporate Services color #8E44AD", '"Corporate Services": "#8E44AD"' in html),
    ("Corporate Services in dropdown", "Corporate Services</option>" in html),
    ("Revenue / FTE KPI logic", "Revenue / FTE" in html),
    ("EBITDA / FTE KPI logic", "EBITDA / FTE" in html),
    ("updateTimeRangeLabels function", "updateTimeRangeLabels" in html),
    ("BLS hidden on division page", 'blsOpt.style.display = "none"' in html),
    ("Utilization avg logic", 'metric === "Utilization" && timeRange !== "Month"' in html),
    ("Contextual time labels", "monthNames[last.getMonth()]" in html),
    ("value= on time range options", 'value="Month"' in html),
]
print("\nVerification:")
all_pass = True
for name, result in checks:
    status = "PASS" if result else "FAIL"
    if not result: all_pass = False
    print(f"  {status}: {name}")
print(f"\nAll checks passed: {all_pass}")
