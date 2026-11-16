/* Interactions select locally prepared estimates, scenarios and SVG coordinates. */
(() => {
  "use strict";
  const byId = id => document.getElementById(id);
  const money = value => (value < 0 ? "−" : "") + "CAD " + Math.abs(value).toLocaleString("en-CA", {maximumFractionDigits: 0});
  const percent = value => value.toFixed(1) + "%";
  const escape = value => String(value).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const svg = (body, label, height = 300) => '<svg viewBox="0 0 760 ' + height + '" role="group" aria-label="' + label + '">' + body + '</svg>';
  const axisText = (x, y, text, anchor = "middle") => '<text class="axis-label" x="' + x + '" y="' + y + '" text-anchor="' + anchor + '">' + text + '</text>';
  function options(select, items, value) {
    select.replaceChildren(...items.map(item => {
      const option = document.createElement("option");
      option.value = item.value; option.textContent = item.label;
      return option;
    }));
    select.value = String(value); select.disabled = false;
  }
  function activate(event, selector, callback) {
    const target = event.target.closest(selector);
    if (target && (event.type === "click" || event.key === "Enter" || event.key === " ")) {
      if (event.type === "keydown") event.preventDefault();
      callback(target);
    }
  }

  async function init() {
    const response = await fetch("assets/visuals-data.json");
    if (!response.ok) throw new Error("The saved chart data could not be loaded.");
    const data = await response.json();
    const regional = data.regional;
    let mapYear = String(regional.latest_year), region = "35", trendYear = "2025";
    let cashPrice = String(data.cash.default_price), allowance = String(data.cash.default_allowance);
    let mapSvg;
    const setMapView = box => mapSvg.setAttribute("viewBox", box.join(" "));
    options(byId("map-year"), regional.years.map(year => ({value: year, label: year})), mapYear);
    options(byId("map-region"), data.map.features.map(f => ({value: f.code, label: f.name})), region);
    const paths = data.map.features.map(f =>
      '<path class="province" data-region="' + f.code + '" d="' + f.path + '" fill-rule="evenodd" role="button" tabindex="0"><title>' + escape(f.name) + '</title></path>'
    ).join("");
    byId("map-stage").innerHTML =
      '<svg id="canada-map" viewBox="' + data.map.view_provinces.join(" ") + '" role="group" aria-label="Interactive map of renter core housing need" aria-describedby="map-definition">' +
      '<defs><pattern id="missing-pattern" patternUnits="userSpaceOnUse" width="6" height="6"><rect width="6" height="6" class="missing-base"/><path d="M-1,1L1,-1M0,6L6,0M5,7L7,5" class="missing-stripe"/></pattern></defs>' +
      paths + '</svg><div id="map-tooltip" class="map-tooltip" aria-hidden="true" hidden></div>';
    mapSvg = byId("canada-map");

    function renderMap() {
      const records = regional.records[mapYear], selected = records[region], national = regional.national[mapYear];
      byId("map-region").value = region;
      byId("map-year").value = mapYear;
      mapSvg.querySelectorAll(".province").forEach(path => {
        const item = records[path.dataset.region], available = item.value !== null;
        path.style.setProperty("--region-light", available ? item.fill_light : "url(#missing-pattern)");
        path.style.setProperty("--region-dark", available ? item.fill_dark : "url(#missing-pattern)");
        path.classList.toggle("selected", item.code === region);
        path.setAttribute("aria-pressed", String(item.code === region));
        const label = item.name + ": " + (available ? percent(item.value) + " of renter households in core housing need, " + mapYear : item.note);
        path.setAttribute("aria-label", label); path.querySelector("title").textContent = label;
      });
      if (selected.value === null) {
        byId("region-detail").innerHTML = '<p class="detail-period">' + mapYear + ' survey</p><h3>' + escape(selected.name) +
          '</h3><p class="region-value unavailable">No estimate</p><p class="small">' + escape(selected.note) + '. This is not a zero.</p>';
      } else {
        const difference = selected.difference_pp;
        const comparison = difference === 0 ? "Matches the published national estimate." :
          Math.abs(difference).toFixed(1) + " percentage points " + (difference > 0 ? "above" : "below") + " the national estimate.";
        const interval = selected.low === null || selected.high === null ? "Confidence interval unavailable." :
          "Published 95% interval: " + percent(selected.low) + "–" + percent(selected.high) + ".";
        byId("region-detail").innerHTML = '<p class="detail-period">' + mapYear + ' survey · Renter households</p><h3>' + escape(selected.name) +
          '</h3><p class="region-value">' + percent(selected.value) + '</p><p class="small">' + interval + '</p><p class="region-comparison">' +
          comparison + '</p><p class="small">Canada, ten provinces: ' + percent(national.value) + '.</p>';
      }
      const sorted = Object.values(records).filter(item => Number(item.code) < 60).sort((a, b) => (b.value ?? -1) - (a.value ?? -1) || a.name.localeCompare(b.name));
      byId("province-bars").innerHTML = sorted.map(item =>
        '<button type="button" class="province-bar' + (item.code === region ? ' selected' : '') + '" data-region="' + item.code + '" aria-pressed="' + (item.code === region) +
        '" aria-label="' + escape(item.name) + ', ' + (item.value === null ? 'not available' : percent(item.value)) + '">' +
        '<span class="bar-name">' + escape(item.name) + '</span><span class="bar-track" aria-hidden="true"><span style="width:' + (item.bar_pct ?? 0) +
        '%"></span></span><span class="bar-value">' + (item.value === null ? 'N/A' : percent(item.value)) + '</span></button>'
      ).join("");
      byId("map-zoom").disabled = false;
    }
    function chooseRegion(code) {
      region = code; renderMap();
      if (Number(code) >= 60) setMapView(data.map.view_all);
    }
    byId("map-year").addEventListener("change", event => {mapYear = event.target.value; renderMap();});
    byId("map-region").addEventListener("change", event => chooseRegion(event.target.value));
    for (const name of ["click", "keydown"]) mapSvg.addEventListener(name, event => activate(event, "[data-region]", target => chooseRegion(target.dataset.region)));
    byId("province-bars").addEventListener("click", event => activate(event, "[data-region]", target => chooseRegion(target.dataset.region)));
    const tooltip = byId("map-tooltip");
    mapSvg.addEventListener("pointermove", event => {
      const target = event.target.closest(".province");
      if (!target) {tooltip.hidden = true; return;}
      const record = regional.records[mapYear][target.dataset.region];
      tooltip.textContent = record.name + " · " + (record.value === null ? "Outside coverage" : percent(record.value));
      tooltip.hidden = false;
    });
    mapSvg.addEventListener("pointerleave", () => {tooltip.hidden = true;});
    byId("map-provinces").addEventListener("click", () => setMapView(data.map.view_provinces));
    byId("map-canada").addEventListener("click", () => setMapView(data.map.view_all));
    byId("map-zoom").addEventListener("click", () => {
      const feature = data.map.features.find(f => f.code === region);
      const [x, y, width, height] = feature.box, pad = Math.max(width, height, 12) * 0.12;
      setMapView([x - pad, y - pad, Math.max(width, 3) + 2 * pad, Math.max(height, 3) + 2 * pad]);
    });
    ["map-provinces", "map-canada"].forEach(id => {byId(id).disabled = false;});
    renderMap();

    options(byId("trend-year"), data.trend.records.map(r => ({value: r.year, label: r.year})), trendYear);
    const trendGrid = data.trend.ticks.map(t => '<line class="grid-line" x1="70" x2="720" y1="' + t.y + '" y2="' + t.y + '"/>' + axisText(57, t.y + 4, t.label, "end")).join("");
    const trendPoints = data.trend.records.map(r =>
      axisText(r.x, 276, r.year) + '<circle class="trend-income-point chart-point" data-year="' + r.year + '" cx="' + r.x + '" cy="' + r.income_y +
      '" r="6" tabindex="0" role="button" aria-label="' + r.year + ', income ' + money(r.income) + ', consumption ' + money(r.consumption) + '"/>' +
      '<circle class="trend-consumption-point" data-year="' + r.year + '" cx="' + r.x + '" cy="' + r.consumption_y + '" r="4"/>'
    ).join("");
    byId("trend-chart").innerHTML = svg(axisText(70, 16, "CAD per household", "start") + trendGrid +
      '<path class="gap-area" d="' + data.trend.gap_area + '"/><path class="income-line" d="' + data.trend.income_path +
      '"/><path class="consumption-line" d="' + data.trend.consumption_path + '"/><line id="trend-marker" class="chart-marker" y1="30" y2="245"/>' + trendPoints,
      "National renter income and consumption from 2020 to 2025");
    function renderTrend() {
      const record = data.trend.records.find(r => String(r.year) === trendYear);
      byId("trend-year").value = trendYear;
      byId("trend-marker").setAttribute("x1", record.x); byId("trend-marker").setAttribute("x2", record.x);
      byId("trend-chart").querySelectorAll("[data-year]").forEach(point => {
        const selected = point.dataset.year === trendYear;
        point.classList.toggle("selected", selected);
        if (point.getAttribute("role") === "button") point.setAttribute("aria-pressed", String(selected));
      });
      byId("trend-readout").innerHTML = '<div><span>' + record.year + ' income</span><strong>' + money(record.income) +
        '</strong></div><div><span>Consumption</span><strong>' + money(record.consumption) +
        '</strong></div><div><span>Income less consumption</span><strong class="' + (record.gap < 0 ? 'negative' : '') + '">' + money(record.gap) +
        '</strong></div><div><span>Reported net saving*</span><strong>' + money(record.saving) + '</strong></div>' +
        '<p class="readout-footnote">*Includes the pension-entitlement adjustment.</p>';
    }
    byId("trend-year").addEventListener("change", event => {trendYear = event.target.value; renderTrend();});
    for (const name of ["click", "keydown"]) byId("trend-chart").addEventListener(name, event => activate(event, "[data-year]", target => {trendYear = target.dataset.year; renderTrend();}));
    renderTrend();

    options(byId("cash-price"), data.cash.prices.map(price => ({value: price, label: money(price)})), cashPrice);
    options(byId("cash-allowance"), data.cash.allowances.map(value => ({value, label: value + "%"})), allowance);
    const cashGrid = data.cash.y_ticks.map(t => '<line class="grid-line" x1="70" x2="720" y1="' + t.y + '" y2="' + t.y + '"/>' + axisText(57, t.y + 4, t.label, "end")).join("");
    function renderCash() {
      const series = data.cash.series[allowance], record = series.records.find(r => String(r.price) === cashPrice);
      byId("cash-price").value = cashPrice; byId("cash-allowance").value = allowance;
      const points = series.records.map(r => '<circle class="cash-point chart-point' + (String(r.price) === cashPrice ? ' selected' : '') +
        '" data-price="' + r.price + '" cx="' + r.x + '" cy="' + r.y + '" r="5" role="button" tabindex="0" aria-pressed="' + (String(r.price) === cashPrice) +
        '" aria-label="Price ' + money(r.price) + ', upfront cash ' + money(r.total) + '"><title>' + money(r.price) + ' home: ' + money(r.total) + ' cash</title></circle>').join("");
      byId("cash-chart").innerHTML = svg(axisText(70, 16, "Upfront cash · CAD", "start") + cashGrid +
        '<line class="threshold-line" x1="' + data.cash.threshold_x + '" x2="' + data.cash.threshold_x + '" y1="30" y2="245"/>' +
        series.paths.map(d => '<path class="cash-line" d="' + d + '"/>').join("") + points +
        data.cash.x_ticks.map(t => axisText(t.x, 270, t.label)).join("") + axisText(395, 297, "Illustrative purchase price · CAD"),
        "Upfront cash scenarios by purchase price; minimum down payment plus assumed closing allowance");
      byId("cash-readout").innerHTML = '<p class="selected-price">' + money(record.price) + ' purchase</p><dl class="calculation">' +
        '<div><dt>Minimum down payment</dt><dd data-metric="minimum_down_payment">' + money(record.down) + '</dd></div>' +
        '<div><dt>Closing allowance, ' + allowance + '%</dt><dd data-metric="closing_allowance">' + money(record.closing) + '</dd></div>' +
        '<div class="total"><dt>Cash in this scenario</dt><dd data-metric="upfront_cash_scenario">' + money(record.total) + '</dd></div></dl>' +
        '<div class="cash-split" aria-hidden="true"><span style="width:' + record.down_share_pct + '%"></span><span style="width:' +
        record.closing_share_pct + '%"></span></div><p class="split-key"><span>Minimum down</span><span>Assumed closing costs</span></p>';
    }
    byId("cash-price").addEventListener("change", event => {cashPrice = event.target.value; renderCash();});
    byId("cash-allowance").addEventListener("change", event => {allowance = event.target.value; renderCash();});
    // Keep focus on the selected SVG control when the chart is redrawn.
    for (const name of ["click", "keydown"]) byId("cash-chart").addEventListener(name, event => activate(event, "[data-price]", target => {
      cashPrice = target.dataset.price; renderCash();
      byId("cash-chart").querySelector('[data-price="' + cashPrice + '"]').focus({preventScroll: true});
    }));
    renderCash();
    document.documentElement.dataset.visuals = "ready";
  }
  init().catch(error => {
    document.documentElement.dataset.visuals = "error";
    const message = byId("visual-error");
    message.textContent = "The interactive data could not load. Please refresh, or use the linked CSV files and Power BI report.";
    message.hidden = false;
    console.error(error);
  });
})();
