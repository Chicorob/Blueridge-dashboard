"""
Patch BlueRidge Life Sciences Dashboard v2_7 -> v2
Applies all 5 requested changes:
  1. Prior year comparison (same dates, one year back)
  2. Calendar-aligned quarter (not rolling 91 days)
  3. Consistent currency units
  4. Consistent aggregation across all pages
  5. Month-based selection (month pickers instead of date pickers)
"""

import os, sys

inpath = r"C:\Users\RobSchulz\OneDrive - Suttons Creek, Inc\Desktop\BlueRidge Life Sciences Dashboardv2_7.html"
outpath = r"C:\Users\RobSchulz\OneDrive - Suttons Creek, Inc\Desktop\BlueRidge Life Sciences Dashboard v2.html"

with open(inpath, "r", encoding="utf-8") as f:
    html = f.read()

# ============================================================
# CHANGE 1 & 2: Replace filterByTimeRange with calendar-month-aligned version
# ============================================================

old_filterByTimeRange = """function filterByTimeRange(timeRange) {
  const dates = dashboardData.dates;
  const last = dates[dates.length - 1];

  // Custom Range uses the date picker values
  if (timeRange === "Custom Range") {
    const startEl = document.getElementById("customStart");
    const endEl = document.getElementById("customEnd");
    if (startEl && endEl && startEl.value && endEl.value) {
      const startDate = new Date(startEl.value + "T00:00:00");
      const endDate = new Date(endEl.value + "T23:59:59");
      const indices = [];
      for (let i = 0; i < dates.length; i++) {
        if (dates[i] >= startDate && dates[i] <= endDate) indices.push(i);
      }
      return indices.length ? indices : [dates.length - 1]; // fallback to latest if empty
    }
    // Fallback: last 91 days if pickers not yet set
    const cutoff = new Date(last); cutoff.setDate(cutoff.getDate() - 91);
    const indices = [];
    for (let i = 0; i < dates.length; i++) { if (dates[i] >= cutoff) indices.push(i); }
    return indices;
  }

  let cutoff;
  if (timeRange === "Month") {
    cutoff = new Date(last); cutoff.setDate(cutoff.getDate() - 30);
  } else if (timeRange === "Quarter") {
    cutoff = new Date(last); cutoff.setDate(cutoff.getDate() - 91);
  } else if (timeRange === "Current Year") {
    cutoff = new Date(last.getFullYear(), 0, 1);
  } else {
    // Trailing 12 Months
    cutoff = new Date(last); cutoff.setDate(cutoff.getDate() - 365);
  }
  const indices = [];
  for (let i = 0; i < dates.length; i++) {
    if (dates[i] >= cutoff) indices.push(i);
  }
  return indices;
}"""

new_filterByTimeRange = """function filterByTimeRange(timeRange) {
  const dates = dashboardData.dates;
  const last = dates[dates.length - 1];

  // Custom Range uses the month picker values
  if (timeRange === "Custom Range") {
    const startEl = document.getElementById("customStart");
    const endEl = document.getElementById("customEnd");
    if (startEl && endEl && startEl.value && endEl.value) {
      const [sy, sm] = startEl.value.split("-").map(Number);
      const [ey, em] = endEl.value.split("-").map(Number);
      const startDate = new Date(sy, sm - 1, 1);
      const endDate = new Date(ey, em, 0, 23, 59, 59); // last day of end month
      const indices = [];
      for (let i = 0; i < dates.length; i++) {
        if (dates[i] >= startDate && dates[i] <= endDate) indices.push(i);
      }
      return indices.length ? indices : [dates.length - 1];
    }
    // Fallback: current quarter
    const qStart = Math.floor(last.getMonth() / 3) * 3;
    const cutoff = new Date(last.getFullYear(), qStart, 1);
    const indices = [];
    for (let i = 0; i < dates.length; i++) { if (dates[i] >= cutoff) indices.push(i); }
    return indices;
  }

  let cutoff;
  if (timeRange === "Month") {
    // Current calendar month only
    cutoff = new Date(last.getFullYear(), last.getMonth(), 1);
  } else if (timeRange === "Quarter") {
    // Current calendar quarter (e.g. Q1 = Jan 1, not rolling 91 days)
    const qStartMonth = Math.floor(last.getMonth() / 3) * 3;
    cutoff = new Date(last.getFullYear(), qStartMonth, 1);
  } else if (timeRange === "Current Year") {
    cutoff = new Date(last.getFullYear(), 0, 1);
  } else {
    // Trailing 12 Months: 12 calendar months ending at latest month
    cutoff = new Date(last.getFullYear(), last.getMonth() - 11, 1);
  }
  const indices = [];
  for (let i = 0; i < dates.length; i++) {
    if (dates[i] >= cutoff) indices.push(i);
  }
  return indices;
}"""

html = html.replace(old_filterByTimeRange, new_filterByTimeRange)

# ============================================================
# CHANGE 1: Replace getPriorPeriodIndices with prior YEAR comparison
# ============================================================

old_getPriorPeriodIndices = """function getPriorPeriodIndices(timeRange) {
  const dates = dashboardData.dates;
  const last = dates[dates.length - 1];
  let days;

  if (timeRange === "Custom Range") {
    const startEl = document.getElementById("customStart");
    const endEl = document.getElementById("customEnd");
    if (startEl && endEl && startEl.value && endEl.value) {
      const startDate = new Date(startEl.value + "T00:00:00");
      const endDate = new Date(endEl.value + "T23:59:59");
      days = Math.max(1, Math.round((endDate - startDate) / 86400000));
      const cutoffEnd = new Date(startDate);
      cutoffEnd.setDate(cutoffEnd.getDate() - 1);
      const cutoffStart = new Date(cutoffEnd);
      cutoffStart.setDate(cutoffStart.getDate() - days);
      const indices = [];
      for (let i = 0; i < dates.length; i++) {
        if (dates[i] >= cutoffStart && dates[i] <= cutoffEnd) indices.push(i);
      }
      return indices;
    }
    days = 91; // fallback
  } else if (timeRange === "Month") days = 30;
  else if (timeRange === "Quarter") days = 91;
  else if (timeRange === "Current Year") {
    days = Math.floor((last - new Date(last.getFullYear(), 0, 1)) / 86400000);
  } else days = 365;

  const cutoffEnd = new Date(last); cutoffEnd.setDate(cutoffEnd.getDate() - days);
  const cutoffStart = new Date(cutoffEnd); cutoffStart.setDate(cutoffStart.getDate() - days);
  const indices = [];
  for (let i = 0; i < dates.length; i++) {
    if (dates[i] >= cutoffStart && dates[i] < cutoffEnd) indices.push(i);
  }
  return indices;
}"""

new_getPriorPeriodIndices = """function getPriorPeriodIndices(timeRange) {
  // Prior year comparison: same date range, shifted back 1 year
  const dates = dashboardData.dates;
  const last = dates[dates.length - 1];
  let start, end;

  if (timeRange === "Custom Range") {
    const startEl = document.getElementById("customStart");
    const endEl = document.getElementById("customEnd");
    if (startEl && endEl && startEl.value && endEl.value) {
      const [sy, sm] = startEl.value.split("-").map(Number);
      const [ey, em] = endEl.value.split("-").map(Number);
      start = new Date(sy - 1, sm - 1, 1);
      end = new Date(ey - 1, em, 0, 23, 59, 59);
    } else {
      const qStart = Math.floor(last.getMonth() / 3) * 3;
      start = new Date(last.getFullYear() - 1, qStart, 1);
      end = new Date(last.getFullYear() - 1, last.getMonth(), last.getDate());
    }
  } else if (timeRange === "Month") {
    start = new Date(last.getFullYear() - 1, last.getMonth(), 1);
    end = new Date(last.getFullYear() - 1, last.getMonth() + 1, 0, 23, 59, 59);
  } else if (timeRange === "Quarter") {
    const qStartMonth = Math.floor(last.getMonth() / 3) * 3;
    start = new Date(last.getFullYear() - 1, qStartMonth, 1);
    end = new Date(last.getFullYear() - 1, last.getMonth(), last.getDate());
  } else if (timeRange === "Current Year") {
    start = new Date(last.getFullYear() - 1, 0, 1);
    end = new Date(last.getFullYear() - 1, last.getMonth(), last.getDate());
  } else {
    // Trailing 12 Months
    start = new Date(last.getFullYear() - 1, last.getMonth() - 11, 1);
    end = new Date(last.getFullYear() - 1, last.getMonth(), last.getDate());
  }

  const indices = [];
  for (let i = 0; i < dates.length; i++) {
    if (dates[i] >= start && dates[i] <= end) indices.push(i);
  }
  return indices;
}"""

html = html.replace(old_getPriorPeriodIndices, new_getPriorPeriodIndices)

# ============================================================
# CHANGE 3: Consistent currency units - update formatValue and kpiCardHTML
# ============================================================

old_formatValue = """function formatValue(val, metric) {
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

new_formatValue = """function formatValue(val, metric, unit) {
  if (metric === "FTE") return val.toFixed(1);
  if (CONFIG.COUNT_METRICS.includes(metric)) return Math.round(val).toLocaleString();
  if (CONFIG.PERCENT_METRICS.includes(metric)) return val.toFixed(1) + "%";
  if (metric === "Revenue / FTE" || metric === "EBITDA / FTE") {
    if (unit === "M") return "$" + (val / 1e6).toFixed(1) + "M";
    if (unit === "K") return "$" + (val / 1e3).toFixed(1) + "K";
    if (Math.abs(val) >= 1e6) return "$" + (val / 1e6).toFixed(1) + "M";
    if (Math.abs(val) >= 1e3) return "$" + (val / 1e3).toFixed(1) + "K";
    return "$" + Math.round(val).toLocaleString();
  }
  // If a forced unit is provided, use it for consistency
  if (unit === "M") return "$" + (val / 1e6).toFixed(1) + "M";
  if (unit === "K") return "$" + Math.round(val / 1e3).toLocaleString() + "K";
  if (Math.abs(val) >= 1e6) return "$" + (val / 1e6).toFixed(1) + "M";
  if (Math.abs(val) >= 1e3) return "$" + Math.round(val / 1e3).toLocaleString() + "K";
  return "$" + Math.round(val).toLocaleString();
}

function determineDisplayUnit(values) {
  // Pick a consistent unit for a set of currency values
  var maxAbs = 0;
  for (var i = 0; i < values.length; i++) {
    var a = Math.abs(values[i]);
    if (a > maxAbs) maxAbs = a;
  }
  return maxAbs >= 1e6 ? "M" : "K";
}"""

html = html.replace(old_formatValue, new_formatValue)

# ============================================================
# CHANGE 3 (cont): Update KPI rendering to use consistent units
# ============================================================

old_renderKPICards = """function renderKPICards(container, entity, timeRange) {
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

new_renderKPICards = """function renderKPICards(container, entity, timeRange) {
  const kpis = getKPIs(entity, timeRange);
  // Determine consistent display unit for all currency values
  var currencyVals = [];
  kpis.forEach(function(k) {
    if (CONFIG.CURRENCY_METRICS.includes(k.metric) || k.metric === "Revenue / FTE" || k.metric === "EBITDA / FTE") {
      currencyVals.push(k.current);
    }
  });
  var displayUnit = determineDisplayUnit(currencyVals);
  // Render in rows of 4
  let html = '';
  for (let r = 0; r < Math.ceil(kpis.length / 4); r++) {
    const rowKpis = kpis.slice(r * 4, r * 4 + 4);
    html += '<div class="kpi-row" style="grid-template-columns:repeat(' + rowKpis.length + ',1fr);">';
    rowKpis.forEach(k => { html += kpiCardHTML(k, displayUnit); });
    html += '</div>';
  }
  container.innerHTML = html;
}"""

html = html.replace(old_renderKPICards, new_renderKPICards)

# Update kpiCardHTML to accept and use unit parameter
old_kpiCardHTML = """function kpiCardHTML(k) {
  const cls = k.delta > 0.5 ? "positive" : k.delta < -0.5 ? "negative" : "neutral";
  const arrow = k.delta > 0.5 ? "\\u25B2" : k.delta < -0.5 ? "\\u25BC" : "\\u25CF";
  return `<div class="kpi-card">
    <div class="kpi-label">${k.metric}</div>
    <div class="kpi-value">${formatValue(k.current, k.metric)}</div>
    <div class="kpi-delta ${cls}">${arrow} ${Math.abs(k.delta).toFixed(1)}% vs prior period</div>
    <div class="kpi-source">Source: ${k.source}</div>
  </div>`;
}"""

new_kpiCardHTML = """function kpiCardHTML(k, displayUnit) {
  const cls = k.delta > 0.5 ? "positive" : k.delta < -0.5 ? "negative" : "neutral";
  const arrow = k.delta > 0.5 ? "\\u25B2" : k.delta < -0.5 ? "\\u25BC" : "\\u25CF";
  const isCurrency = CONFIG.CURRENCY_METRICS.includes(k.metric) || k.metric === "Revenue / FTE" || k.metric === "EBITDA / FTE";
  const unit = isCurrency ? displayUnit : undefined;
  return `<div class="kpi-card">
    <div class="kpi-label">${k.metric}</div>
    <div class="kpi-value">${formatValue(k.current, k.metric, unit)}</div>
    <div class="kpi-delta ${cls}">${arrow} ${Math.abs(k.delta).toFixed(1)}% vs prior year</div>
    <div class="kpi-source">Source: ${k.source}</div>
  </div>`;
}"""

html = html.replace(old_kpiCardHTML, new_kpiCardHTML)

# ============================================================
# CHANGE 4: Remove special Utilization averaging in getKPIs
# (It should use the same point-in-time logic as other metrics)
# ============================================================

old_utilAvg = """    // Utilization: show average over time range unless Month is selected
    if (metric === "Utilization" && timeRange !== "Month") {
      const currVals = currIdx.map(i => data[metric][i]);
      current = currVals.length ? currVals.reduce((a, b) => a + b, 0) / currVals.length : 0;
      const priorVals = priorIdx.map(i => data[metric][i]);
      prior = priorVals.length ? priorVals.reduce((a, b) => a + b, 0) / priorVals.length : 0;
    }"""

new_utilAvg = """    // All point-in-time metrics (including Utilization) use latest value consistently"""

html = html.replace(old_utilAvg, new_utilAvg)

# ============================================================
# CHANGE 5: Replace date pickers with month pickers in sidebar
# ============================================================

old_customRange = """    <div class="sidebar-select-group hidden" id="customRangeGroup">
      <label>Start Date</label>
      <input type="date" id="customStart" style="width:100%;padding:8px 10px;border-radius:6px;border:1px solid rgba(255,255,255,0.2);background:rgba(255,255,255,0.08);color:#fff;font-family:inherit;font-size:13px;">
      <label style="margin-top:8px;">End Date</label>
      <input type="date" id="customEnd" style="width:100%;padding:8px 10px;border-radius:6px;border:1px solid rgba(255,255,255,0.2);background:rgba(255,255,255,0.08);color:#fff;font-family:inherit;font-size:13px;">
      <button class="btn-primary" id="applyCustomRange" style="width:100%;margin-top:8px;padding:8px;font-size:13px;">Apply Range</button>
    </div>"""

new_customRange = """    <div class="sidebar-select-group hidden" id="customRangeGroup">
      <label>Start Month</label>
      <select id="customStart" style="width:100%;padding:8px 10px;border-radius:6px;border:1px solid rgba(255,255,255,0.2);background:rgba(255,255,255,0.08);color:#fff;font-family:inherit;font-size:13px;"></select>
      <label style="margin-top:8px;">End Month</label>
      <select id="customEnd" style="width:100%;padding:8px 10px;border-radius:6px;border:1px solid rgba(255,255,255,0.2);background:rgba(255,255,255,0.08);color:#fff;font-family:inherit;font-size:13px;"></select>
      <button class="btn-primary" id="applyCustomRange" style="width:100%;margin-top:8px;padding:8px;font-size:13px;">Apply Range</button>
    </div>"""

html = html.replace(old_customRange, new_customRange)

# ============================================================
# CHANGE 5 (cont): Update event listener for custom range defaults
# ============================================================

old_timeRangeListener = """document.getElementById("timeRange").addEventListener("change", e => {
  selectedTimeRange = e.target.value;
  const customGroup = document.getElementById("customRangeGroup");
  if (selectedTimeRange === "Custom Range") {
    customGroup.classList.remove("hidden");
    // Set sensible defaults if empty
    const startEl = document.getElementById("customStart");
    const endEl = document.getElementById("customEnd");
    if (!startEl.value) {
      const d = new Date(); d.setDate(d.getDate() - 91);
      startEl.value = d.toISOString().split("T")[0];
    }
    if (!endEl.value) {
      endEl.value = new Date().toISOString().split("T")[0];
    }
  } else {
    customGroup.classList.add("hidden");
  }
  document.getElementById("headerSub").textContent = selectedEntity + " | " + getTimeRangeLabel();
  if (selectedTimeRange !== "Custom Range") renderCurrentPage();
});"""

new_timeRangeListener = """document.getElementById("timeRange").addEventListener("change", e => {
  selectedTimeRange = e.target.value;
  const customGroup = document.getElementById("customRangeGroup");
  if (selectedTimeRange === "Custom Range") {
    customGroup.classList.remove("hidden");
    populateMonthPickers();
  } else {
    customGroup.classList.add("hidden");
  }
  document.getElementById("headerSub").textContent = selectedEntity + " | " + getTimeRangeLabel();
  if (selectedTimeRange !== "Custom Range") renderCurrentPage();
});

function populateMonthPickers() {
  if (!dashboardData) return;
  var startEl = document.getElementById("customStart");
  var endEl = document.getElementById("customEnd");
  // Only populate if empty (first time)
  if (startEl.options.length > 0) return;
  var mn = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  var seen = {};
  var months = [];
  dashboardData.dates.forEach(function(d) {
    var key = d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0");
    if (!seen[key]) {
      seen[key] = true;
      months.push({ y: d.getFullYear(), m: d.getMonth() + 1, key: key,
                     label: mn[d.getMonth()] + " " + d.getFullYear() });
    }
  });
  months.sort(function(a, b) { return a.key < b.key ? -1 : 1; });
  months.forEach(function(mo) {
    startEl.add(new Option(mo.label, mo.key));
    endEl.add(new Option(mo.label, mo.key));
  });
  // Default: start = first month, end = last month
  if (months.length > 0) {
    startEl.value = months[0].key;
    endEl.value = months[months.length - 1].key;
  }
}"""

html = html.replace(old_timeRangeListener, new_timeRangeListener)

# ============================================================
# CHANGE 5 (cont): Update getTimeRangeLabel for month format
# ============================================================

old_getTimeRangeLabel = """function getTimeRangeLabel() {
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

new_getTimeRangeLabel = """function getTimeRangeLabel() {
  var mn = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  if (selectedTimeRange === "Custom Range") {
    var s = document.getElementById("customStart");
    var e = document.getElementById("customEnd");
    if (s && e && s.value && e.value) {
      var sp = s.value.split("-").map(Number);
      var ep = e.value.split("-").map(Number);
      return mn[sp[1]-1] + " " + sp[0] + " \\u2013 " + mn[ep[1]-1] + " " + ep[0];
    }
    return "Custom Range";
  }
  if (dashboardData) {
    var last = dashboardData.dates[dashboardData.dates.length - 1];
    var yr = last.getFullYear();
    if (selectedTimeRange === "Month") return mn[last.getMonth()] + " " + yr;
    if (selectedTimeRange === "Quarter") return "Q" + (Math.floor(last.getMonth() / 3) + 1) + " " + yr;
    if (selectedTimeRange === "Current Year") return "YTD " + yr;
    if (selectedTimeRange === "Trailing 12 Months") {
      var startM = new Date(yr, last.getMonth() - 11, 1);
      return mn[startM.getMonth()] + " " + startM.getFullYear() + " \\u2013 " + mn[last.getMonth()] + " " + yr;
    }
  }
  return selectedTimeRange;
}"""

html = html.replace(old_getTimeRangeLabel, new_getTimeRangeLabel)

# ============================================================
# Update "vs prior period" -> "vs prior year" everywhere
# ============================================================
html = html.replace("vs prior period", "vs prior year")

# ============================================================
# Update title to v2
# ============================================================
html = html.replace("<title>BlueRidge Life Sciences Dashboard</title>",
                    "<title>BlueRidge Life Sciences Dashboard v2</title>")

# Write output
with open(outpath, "w", encoding="utf-8") as f:
    f.write(html)

size_mb = os.path.getsize(outpath) / (1024*1024)
print(f"Created: {outpath}")
print(f"Size: {size_mb:.1f} MB")

# ============================================================
# Verification
# ============================================================
checks = [
    ("Calendar month filtering", "new Date(last.getFullYear(), last.getMonth(), 1)" in html),
    ("Calendar quarter filtering", "Math.floor(last.getMonth() / 3) * 3" in html),
    ("Prior year comparison", "// Prior year comparison: same date range, shifted back 1 year" in html),
    ("Prior year uses getFullYear()-1", "last.getFullYear() - 1" in html),
    ("formatValue accepts unit param", "function formatValue(val, metric, unit)" in html),
    ("determineDisplayUnit function", "function determineDisplayUnit(values)" in html),
    ("KPI cards use displayUnit", "kpiCardHTML(k, displayUnit)" in html),
    ("kpiCardHTML accepts displayUnit", "function kpiCardHTML(k, displayUnit)" in html),
    ("vs prior year (not period)", "vs prior year" in html),
    ("No more 'vs prior period'", "vs prior period" not in html),
    ("Month pickers (select not date)", '<select id="customStart"' in html),
    ("No date inputs for custom range", 'type="date" id="customStart"' not in html),
    ("populateMonthPickers function", "function populateMonthPickers()" in html),
    ("Utilization special avg removed", 'metric === "Utilization" && timeRange !== "Month"' not in html),
    ("Consistent aggregation note", "All point-in-time metrics (including Utilization) use latest value consistently" in html),
    ("Title says v2", "Dashboard v2" in html),
    ("No rolling 91 days for quarter", "cutoff.getDate() - 91" not in html),
    ("No rolling 30 days for month", "cutoff.getDate() - 30" not in html),
    ("getTimeRangeLabel updated", 'return "YTD " + yr' in html),
]

print("\nVerification:")
all_pass = True
for name, result in checks:
    status = "PASS" if result else "FAIL"
    if not result: all_pass = False
    print(f"  {status}: {name}")
print(f"\nAll checks passed: {all_pass}")
