import { obligation, measure, ranking, csv } from "./core.mjs";
const $ = (id) => document.getElementById(id);
const states = Object.fromEntries(
  "AL:Alabama|AK:Alaska|AZ:Arizona|AR:Arkansas|CA:California|CO:Colorado|CT:Connecticut|DE:Delaware|DC:District of Columbia|FL:Florida|GA:Georgia|HI:Hawaii|ID:Idaho|IL:Illinois|IN:Indiana|IA:Iowa|KS:Kansas|KY:Kentucky|LA:Louisiana|ME:Maine|MD:Maryland|MA:Massachusetts|MI:Michigan|MN:Minnesota|MS:Mississippi|MO:Missouri|MT:Montana|NE:Nebraska|NV:Nevada|NH:New Hampshire|NJ:New Jersey|NM:New Mexico|NY:New York|NC:North Carolina|ND:North Dakota|OH:Ohio|OK:Oklahoma|OR:Oregon|PA:Pennsylvania|RI:Rhode Island|SC:South Carolina|SD:South Dakota|TN:Tennessee|TX:Texas|UT:Utah|VT:Vermont|VA:Virginia|WA:Washington|WV:West Virginia|WI:Wisconsin|WY:Wyoming|AS:American Samoa|GU:Guam|MP:Northern Mariana Islands|PR:Puerto Rico|VI:U.S. Virgin Islands"
    .split("|")
    .map((s) => s.split(":")),
);
const fips = Object.fromEntries(
  "01:AL 02:AK 04:AZ 05:AR 06:CA 08:CO 09:CT 10:DE 11:DC 12:FL 13:GA 15:HI 16:ID 17:IL 18:IN 19:IA 20:KS 21:KY 22:LA 23:ME 24:MD 25:MA 26:MI 27:MN 28:MS 29:MO 30:MT 31:NE 32:NV 33:NH 34:NJ 35:NM 36:NY 37:NC 38:ND 39:OH 40:OK 41:OR 42:PA 44:RI 45:SC 46:SD 47:TN 48:TX 49:UT 50:VT 51:VA 53:WA 54:WV 55:WI 56:WY 60:AS 66:GU 69:MP 72:PR 78:VI"
    .split(" ")
    .map((s) => s.split(":")),
);
const esc = (x) =>
  String(x ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const money = (n) =>
  n == null
    ? "Unavailable"
    : new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        notation: Math.abs(n) >= 1e6 ? "compact" : "standard",
        maximumFractionDigits: Math.abs(n) >= 1e6 ? 2 : 0,
      }).format(n);
const exact = (n) =>
  n == null
    ? "Unavailable"
    : new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 2,
      }).format(n);
const num = (n) => (n == null ? "Unavailable" : n.toLocaleString("en-US"));
let spending,
  geo,
  earmarks,
  rows = [],
  sorted = [],
  selected = null,
  page = 0,
  earPage = 0,
  earFiltered = [],
  zoom,
  paths,
  scale,
  liveSerial = 0;
const palette = [
  "#d9e9ed",
  "#a8d2d8",
  "#6db3c1",
  "#338caa",
  "#146b85",
  "#15425b",
];
const filter = () => ({
  year: $("year").value,
  kind: $("kind").value,
  capita: $("metric").value === "capita",
  state: $("state").value,
});
const stateOf = (r) => r.name?.split("-")[0] || fips[r.id.slice(0, 2)];
const value = (r) => measure(r, filter().kind, filter().capita);
function download(name, content, type = "text/csv;charset=utf-8") {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function mix(r, mini = false) {
  const g = r.grants,
    c = r.contracts,
    total = Math.max(0, g ?? 0) + Math.max(0, c ?? 0);
  if (g == null || c == null)
    return '<span class="tiny">Mix unavailable</span>';
  if (total <= 0) return '<span class="tiny">No positive obligations</span>';
  return `<div class="${mini ? "mini-mix" : "mix-track"}" title="Grants ${exact(g)}; contracts ${exact(c)}"><span class="mix-grants" style="width:${(100 * Math.max(0, g)) / total}%"></span><span class="mix-contracts" style="width:${(100 * Math.max(0, c)) / total}%"></span></div>`;
}
function createMap() {
  const svg = d3.select("#map");
  const viewport = svg.append("g");
  const mainland = geo.features.filter(
    (f) => Number(f.properties.STATEFP) < 60,
  );
  const projection = d3.geoAlbersUsa().translate([480, 270]).scale(1110);
  const path = d3.geoPath(projection);
  paths = viewport
    .append("g")
    .selectAll("path")
    .data(mainland)
    .join("path")
    .attr("d", path);
  // Small outlying areas get independent labeled insets instead of disappearing from a US projection.
  ["72", "78", "66", "69", "60"].forEach((code, i) => {
    const features = geo.features.filter((f) => f.properties.STATEFP === code),
      x = 45 + i * 178;
    const group = viewport.append("g");
    group
      .append("rect")
      .on("click", () => selectDistrict(features[0].properties.GEOID))
      .style("cursor", "pointer")
      .attr("class", "inset-box")
      .attr("x", x)
      .attr("y", 535)
      .attr("width", 160)
      .attr("height", 92);
    const p = d3.geoMercator().fitExtent(
      [
        [x + 12, 548],
        [x + 148, 607],
      ],
      { type: "FeatureCollection", features },
    );
    group
      .selectAll("path")
      .data(features)
      .join("path")
      .attr("d", d3.geoPath(p));
    if (["60", "69"].includes(code)) {
      const center = p(d3.geoCentroid({ type: "FeatureCollection", features }));
      group
        .append("circle")
        .attr("cx", center[0])
        .attr("cy", center[1])
        .attr("r", 7)
        .attr("fill", "none")
        .attr("stroke", "#146b85")
        .attr("stroke-width", 1)
        .attr("aria-hidden", "true")
        .style("pointer-events", "none");
    }
    group
      .append("text")
      .attr("class", "inset-label")
      .attr("x", x + 8)
      .attr("y", 645)
      .text(fips[code]);
  });
  paths = viewport
    .selectAll("path")
    .attr("class", "district")
    .attr("data-id", (d) => d.properties.GEOID)
    .attr(
      "aria-label",
      (d) => `${fips[d.properties.STATEFP]}-${d.properties.CD119FP}`,
    )
    .on("pointermove", (event, d) => showTooltip(event, d))
    .on("pointerleave", () => {
      $("tooltip").hidden = true;
    })
    .on("click", (e, d) => selectDistrict(d.properties.GEOID));
  const labels = viewport.append("g").attr("aria-hidden", "true");
  d3.groups(mainland, (f) => f.properties.STATEFP).forEach(
    ([state, features]) => {
      if (["09", "10", "11", "24", "25", "34", "44"].includes(state)) return;
      const center = projection(
        d3.geoCentroid({ type: "FeatureCollection", features }),
      );
      if (center)
        labels
          .append("text")
          .attr("class", "state-label")
          .attr("x", center[0])
          .attr("y", center[1])
          .text(fips[state]);
    },
  );
  zoom = d3
    .zoom()
    .scaleExtent([1, 14])
    .on("zoom", (e) => {
      viewport.attr("transform", e.transform);
      $("tooltip").hidden = true;
    });
  svg.call(zoom).on("dblclick.zoom", null);
  $("zoom-in").onclick = () => svg.call(zoom.scaleBy, 1.6);
  $("zoom-out").onclick = () => svg.call(zoom.scaleBy, 1 / 1.6);
  $("reset-map").onclick = () => svg.call(zoom.transform, d3.zoomIdentity);
}
function showTooltip(event, feature) {
  const r = rows.find((r) => r.id === feature.properties.GEOID),
    tip = $("tooltip");
  tip.innerHTML = `<strong>${esc(r?.name || `${fips[feature.properties.STATEFP]}-${feature.properties.CD119FP}`)}</strong>${money(value(r))}${filter().capita ? " per resident" : ""}<br><span class="tiny">Click to inspect district</span>`;
  tip.hidden = false;
  const box =
    event.currentTarget.ownerSVGElement.parentElement.getBoundingClientRect();
  tip.style.left = `${Math.max(5, Math.min(event.clientX - box.left + 14, box.width - 195))}px`;
  tip.style.top = `${Math.max(0, Math.min(event.clientY - box.top + 14, box.height - 110))}px`;
}
function render() {
  const f = filter();
  rows = spending.years[f.year].districts;
  const scoped = rows.filter((r) => !f.state || stateOf(r) === f.state);
  sorted = ranking(scoped, f.kind, f.capita);
  const known = scoped.filter((r) => obligation(r, f.kind) != null),
    total = d3.sum(known, (r) => obligation(r, f.kind));
  $("total").textContent = money(total);
  $("total").title = exact(total);
  $("total-label").textContent = f.state
    ? `${f.state} mapped obligations`
    : "Mapped obligations";
  $("district-count").textContent = `${known.length} / ${scoped.length}`;
  $("median").textContent = money(
    d3.median(known, (r) => obligation(r, f.kind)) ?? null,
  );

  $("map-title").textContent = f.capita
    ? "Obligations per resident"
    : "Federal award obligations";
  $("map-subtitle").textContent =
    `FY ${f.year} · ${f.kind === "all" ? "Grants & contracts" : f.kind === "grants" ? "Grants" : "Contracts"} · Place of performance`;
  // Quantiles expose geographic differences without allowing a few large awards to flatten the map.
  const positives = sorted.map(value).filter((v) => v > 0);
  scale = d3.scaleQuantile().domain(positives).range(palette);
  const lookup = new Map(rows.map((r) => [r.id, r]));
  paths
    .attr("fill", (d) => {
      const n = value(lookup.get(d.properties.GEOID));
      return n == null
        ? "#c8d0d6"
        : n < 0
          ? "#ba703b"
          : n === 0
            ? "#fff"
            : scale(n);
    })
    .classed("selected", (d) => d.properties.GEOID === selected)
    .classed("faded", (d) => f.state && fips[d.properties.STATEFP] !== f.state);
  $("legend-title").textContent =
    `${f.capita ? "Per resident" : "Net obligations"} · six equal-count bands`;
  const limits = [0, ...scale.quantiles()];
  $("legend").innerHTML =
    palette
      .map(
        (c, i) =>
          `<span><i style="background:${c}"></i>${i === 0 ? "Over $0" : money(limits[i]) + "+"}</span>`,
      )
      .join("") +
    '<span><i style="background:#fff"></i>$0</span><span><i style="background:#ba703b"></i>Negative</span><span><i style="background:#c8d0d6"></i>Unavailable</span>';
  if (!selected || !scoped.some((r) => r.id === selected))
    selected = sorted[0]?.id ?? null;
  paths.classed("selected", (d) => d.properties.GEOID === selected);
  renderDetail();
  renderRankings();
  renderCoverage();
}
function selectDistrict(id) {
  selected = id;
  paths.classed("selected", (d) => d.properties.GEOID === id);
  renderDetail();
  renderRankings();
}
function renderDetail() {
  const r = rows.find((r) => r.id === selected),
    f = filter();
  liveSerial++;
  if (!r) {
    $("district-detail").innerHTML =
      "<p>Select a district to see its federal award obligations.</p>";
    return;
  }
  const rank = sorted.findIndex((x) => x.id === r.id) + 1;
  const trend = Object.entries(spending.years).map(([year, data]) => ({
    year,
    value: obligation(
      data.districts.find((x) => x.id === r.id),
      f.kind,
    ),
  }));
  const high = d3.max(trend, (d) => Math.abs(d.value ?? 0)) || 1;
  const st = stateOf(r),
    keys = st === "VI" ? ["VI", "USVI"] : [st];
  const stateAmount = d3.sum(keys, (k) => earmarks.states[k]?.amount ?? 0),
    stateProjects = d3.sum(keys, (k) => earmarks.states[k]?.projects ?? 0);
  $("district-detail").innerHTML =
    `<div><div class="district-title"><h2>${esc(r.name)}</h2><span class="rank-tag">${rank ? "#" + rank + " of " + sorted.length : "Outside filter"}</span></div><p class="state-name">${esc(states[st])}${r.name.endsWith("-00") ? " · At-large district" : ""}</p><span class="tiny">Net obligations</span><div class="big-amount" title="${exact(obligation(r, f.kind))}">${money(obligation(r, f.kind))}</div></div>
 <div><div class="detail-stats"><div>Per resident<strong>${money(measure(r, f.kind, true))}</strong></div><div>Reference population<strong>${num(r.population)}</strong></div></div><h3>Award mix</h3>${mix(r)}<div class="mix-label"><span>Grants</span><strong>${money(r.grants)}</strong></div><div class="mix-label"><span>Contracts</span><strong>${money(r.contracts)}</strong></div><p class="tiny">Both award types shown.</p></div>
 <div><h3>Annual obligations</h3><div class="trend" role="img" aria-label="${esc(trend.map((d) => `FY ${d.year}: ${exact(d.value)}`).join("; "))}">${trend.map((d) => `<div class="trend-item ${d.year === f.year ? "current" : ""}" title="FY ${d.year}: ${exact(d.value)}"><div class="trend-bar" style="height:${Math.max(2, (Math.abs(d.value ?? 0) / high) * 65)}px;${d.value < 0 ? "background:#ba703b;" : ""}"></div><span>${d.year}</span></div>`).join("")}</div></div>
 <div class="context-note"><strong>${esc(st)} earmarks · FY2022–2024</strong>${money(stateAmount)} across ${num(stateProjects)} projects.<br>State total; no district allocation.<br><button id="state-earmarks" class="text-button">View projects</button></div>
 <button id="load-live" class="live-button">Agencies & programs</button><div id="live-detail" class="live-section" aria-live="polite"></div>`;
  $("state-earmarks").onclick = () => {
    $("ear-state").value = st === "VI" ? "@VI" : st;
    $("ear-year").value = "";
    $("ear-search").value = "";
    earPage = 0;
    setView("earmarks");
    renderEarmarks();
  };
  $("load-live").onclick = () => loadLive(r, f);
}
async function loadLive(r, f) {
  const serial = ++liveSerial,
    button = $("load-live");
  button.disabled = true;
  button.textContent = "Loading official detail…";
  try {
    const categories = [
      "awarding_agency",
      ...(f.kind === "grants"
        ? ["cfda"]
        : f.kind === "contracts"
          ? ["naics"]
          : ["cfda", "naics"]),
    ];
    const filters = {
      time_period: [
        { start_date: `${+f.year - 1}-10-01`, end_date: `${f.year}-09-30` },
      ],
      award_type_codes: spending.award_type_codes[f.kind] || [
        ...spending.award_type_codes.grants,
        ...spending.award_type_codes.contracts,
      ],
      place_of_performance_locations: [
        {
          country: "USA",
          state: stateOf(r),
          district_current: r.name.split("-")[1],
        },
      ],
    };
    const results = await Promise.all(
      categories.map(async (category) => {
        const response = await fetch(
          `https://api.usaspending.gov/api/v2/search/spending_by_category/${category}/`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              category,
              spending_level: "transactions",
              limit: 6,
              page: 1,
              filters,
            }),
            signal: AbortSignal.timeout(45000),
          },
        );
        if (!response.ok)
          throw Error("USAspending details are temporarily unavailable");
        return [
          category,
          { ...(await response.json()), fetched_at: new Date().toISOString() },
        ];
      }),
    );
    const result = Object.fromEntries(results);
    if (serial !== liveSerial) return;
    $("live-detail").innerHTML =
      Object.entries(result)
        .map(
          ([cat, data]) =>
            `<h3>${cat === "awarding_agency" ? "Top awarding agencies" : cat === "cfda" ? "Top assistance programs (grants)" : "Top industries (contracts)"}</h3>${data.results.length ? data.results.map((item) => `<div class="live-item"><span>${esc(item.name || "Unspecified")}${item.code ? " (" + esc(item.code) + ")" : ""}</span><strong>${money(item.amount)}</strong></div>`).join("") : "<p>No matching results returned.</p>"}`,
        )
        .join("") +
      `<p class="tiny">Top 6 per category, not a full reconciliation. Live data retrieved ${new Date(result.awarding_agency.fetched_at).toLocaleString()}; revisions may differ from the saved map snapshot.</p>`;
    button.textContent = "Refresh details";
  } catch (e) {
    if (serial !== liveSerial) return;
    $("live-detail").innerHTML =
      `<p class="error">${esc(e.message)}. Try again shortly; saved map data remain available.</p>`;
    button.textContent = "Retry details";
  } finally {
    if (serial === liveSerial) button.disabled = false;
  }
}
function renderRankings() {
  const query = $("search").value.trim().toLowerCase().replace(/\s+/g, " ");
  const matches = sorted.filter((r) =>
    `${r.name} ${states[stateOf(r)]}`.toLowerCase().includes(query),
  );
  const pages = Math.max(1, Math.ceil(matches.length / 12));
  page = Math.min(page, pages - 1);
  const start = page * 12;
  $("rankings").innerHTML =
    matches
      .slice(start, start + 12)
      .map(
        (r) =>
          `<tr class="${r.id === selected ? "row-selected" : ""}"><td>${sorted.indexOf(r) + 1}</td><td><button class="district-link" data-select="${r.id}">${esc(r.name)}<span>${esc(states[stateOf(r)])}</span></button></td><td title="${exact(obligation(r, filter().kind))}">${money(obligation(r, filter().kind))}</td><td>${money(measure(r, filter().kind, true))}</td><td>${mix(r, true)}</td></tr>`,
      )
      .join("") ||
    '<tr><td colspan="5" class="empty">No districts match. Try a state name or district code such as AL-05.</td></tr>';
  $("rank-count").textContent = matches.length
    ? `${start + 1}–${Math.min(start + 12, matches.length)} of ${matches.length} districts`
    : "0 districts";
  $("page-number").textContent = `${page + 1} / ${pages}`;
  $("prev").disabled = page === 0;
  $("next").disabled = page >= pages - 1;
  $("rank-subtitle").textContent =
    `${filter().capita ? "Per resident" : "Total net obligations"} · ${filter().state || "All states & territories"}`;
  $("rankings")
    .querySelectorAll("[data-select]")
    .forEach((b) => (b.onclick = () => selectDistrict(b.dataset.select)));
}
function renderCoverage() {
  const f = filter(),
    data = spending.years[f.year],
    kinds = f.kind === "all" ? ["grants", "contracts"] : [f.kind],
    excluded = d3.sum(kinds, (k) =>
      d3.sum(data.unmapped[k], (r) => r.aggregated_amount),
    );
  $("coverage-details").innerHTML =
    `<p><strong>FY ${f.year} snapshot:</strong> ${data.districts.length} matched district areas. ${exact(excluded)} in non-matching rows for ${f.kind === "all" ? "grants and contracts" : f.kind}, excluded from mapped totals. This coverage statement is nationwide, independent of the state filter.</p>`;
}
function setView(view) {
  $("district-view").hidden = view !== "districts";
  $("earmark-view").hidden = view !== "earmarks";
  document.querySelectorAll("[data-view]").forEach((b) => {
    b.classList.toggle("active", b.dataset.view === view);
    b.setAttribute("aria-pressed", b.dataset.view === view);
  });
  if (view === "earmarks") renderEarmarks();
}
function renderEarmarks() {
  const year = $("ear-year").value,
    state = $("ear-state").value,
    query = $("ear-search").value.trim().toLowerCase();
  earFiltered = earmarks.projects
    .filter(
      (p) =>
        (!year || String(p.year) === year) &&
        (!state ||
          (state === "@VI"
            ? ["VI", "USVI"].includes(p.location)
            : p.location === state)) &&
        (!query ||
          `${p.project} ${p.requesters} ${p.agency} ${p.id}`
            .toLowerCase()
            .includes(query)),
    )
    .sort((a, b) => b.amount - a.amount || a.id.localeCompare(b.id));
  const pages = Math.max(1, Math.ceil(earFiltered.length / 15));
  earPage = Math.min(earPage, pages - 1);
  const start = earPage * 15;
  $("ear-total").textContent = money(d3.sum(earFiltered, (p) => p.amount));
  $("ear-total").title = exact(d3.sum(earFiltered, (p) => p.amount));
  $("ear-count").textContent = `${num(earFiltered.length)} unique projects`;
  $("ear-projects").innerHTML =
    earFiltered
      .slice(start, start + 15)
      .map(
        (p) =>
          `<article class="project"><div><div class="project-amount" title="${exact(p.amount)}">${money(p.amount)}</div><div class="project-year">FY ${p.year} · ${esc(p.location)}</div></div><div><h3>${esc(p.project)}</h3><p><b>${esc(p.agency)}</b></p><p>Requesters: ${esc(p.requesters)}</p></div></article>`,
      )
      .join("") ||
    '<p class="empty">No projects match these filters. Try a broader search or another location.</p>';
  $("ear-page-count").textContent = earFiltered.length
    ? `${start + 1}–${Math.min(start + 15, earFiltered.length)} of ${num(earFiltered.length)} projects`
    : "0 projects";
  $("ear-prev").disabled = earPage === 0;
  $("ear-next").disabled = earPage >= pages - 1;
}
function downloadDistricts() {
  const f = filter(),
    header = [
      "row_type",
      "fiscal_year",
      "boundary_congress",
      "district_id",
      "district",
      "state",
      "award_types",
      "net_obligations_usd",
      "population_api_reference",
      "obligations_per_resident",
      "grants_usd",
      "contracts_usd",
      "snapshot_retrieved_at",
    ];
  const result = [
    header,
    ...sorted.map((r) => [
      "district",
      f.year,
      119,
      r.id,
      r.name,
      stateOf(r),
      f.kind,
      obligation(r, f.kind),
      r.population,
      measure(r, f.kind, true),
      r.grants,
      r.contracts,
      spending.fetched_at,
    ]),
  ];
  // Exclusions are national evidence; never silently allocate them to a filtered state.
  if (!f.state)
    for (const k of f.kind === "all" ? ["grants", "contracts"] : [f.kind])
      for (const r of spending.years[f.year].unmapped[k])
        result.push([
          "unmapped",
          f.year,
          119,
          r.shape_code,
          r.display_name,
          "",
          k,
          r.aggregated_amount,
          r.population,
          r.per_capita,
          "",
          "",
          spending.fetched_at,
        ]);
  download(
    `federal-obligations-fy${f.year}-${f.kind}-${f.state || "all"}.csv`,
    csv(result),
  );
}
async function init() {
  try {
    const responses = await Promise.all(
      ["spending.json", "districts.geojson", "earmarks.json"].map((name) =>
        fetch("data/" + name).then((r) => {
          if (!r.ok) throw Error(`Cannot load ${name}`);
          return r.json();
        }),
      ),
    );
    [spending, geo, earmarks] = responses;
    const options = Object.entries(states)
      .sort((a, b) => a[1].localeCompare(b[1]))
      .map(
        ([code, name]) => `<option value="${code}">${name} (${code})</option>`,
      )
      .join("");
    $("state").insertAdjacentHTML("beforeend", options);
    const locations = [
      ...new Set(earmarks.projects.map((p) => p.location)),
    ].sort();
    $("ear-state").insertAdjacentHTML(
      "beforeend",
      locations
        .map(
          (st) =>
            `<option value="${esc(st)}">${esc(states[st] || st)} (${esc(st)})</option>`,
        )
        .join("") +
        '<option value="@VI">U.S. Virgin Islands (VI + USVI)</option>',
    );
    $("snapshot").textContent =
      `Data retrieved ${new Date(spending.fetched_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}`;
    $("freshness").textContent =
      `USAspending snapshots retrieved ${spending.fetched_at}. GAO compilation retrieved ${earmarks.metadata.retrieved_at}. FY2026 has recently ended and agency reporting can still be revised. Figures are nominal dollars.`;
    createMap();
    render();
    $("loading").hidden = true;
    $("app").hidden = false;
    for (const id of ["year", "kind", "metric", "state"])
      $(id).addEventListener("change", () => {
        page = 0;
        render();
      });
    $("search").addEventListener("input", () => {
      page = 0;
      renderRankings();
    });
    $("prev").onclick = () => {
      page--;
      renderRankings();
    };
    $("next").onclick = () => {
      page++;
      renderRankings();
    };
    $("download").onclick = downloadDistricts;
    for (const id of ["ear-year", "ear-state", "ear-search"])
      $(id).addEventListener(id === "ear-search" ? "input" : "change", () => {
        earPage = 0;
        renderEarmarks();
      });
    $("ear-prev").onclick = () => {
      earPage--;
      renderEarmarks();
    };
    $("ear-next").onclick = () => {
      earPage++;
      renderEarmarks();
    };
    $("ear-download").onclick = () =>
      download(
        "gao-earmarks-filtered.csv",
        csv([
          [
            "gao_id",
            "fiscal_year",
            "enacted_appropriation_usd",
            "agency",
            "project_recipient",
            "source_location",
            "requesters",
          ],
          ...earFiltered.map((p) => [
            p.id,
            p.year,
            p.amount,
            p.agency,
            p.project,
            p.location,
            p.requesters,
          ]),
        ]),
      );
    document
      .querySelectorAll("[data-view]")
      .forEach((b) => (b.onclick = () => setView(b.dataset.view)));
  } catch (error) {
    $("loading").innerHTML =
      `<strong>Dashboard data could not load.</strong><p>${esc(error.message)}. Reload the page to try again.</p>`;
    console.error(error);
  }
}
for (const id of ["method-open", "method-inline", "footer-method"])
  $(id).onclick = () => $("method").showModal();
$("method-close").onclick = () => $("method").close();
$("method").addEventListener("click", (e) => {
  if (e.target === $("method")) {
    const r = $("method").getBoundingClientRect();
    if (
      e.clientX < r.left ||
      e.clientX > r.right ||
      e.clientY < r.top ||
      e.clientY > r.bottom
    )
      $("method").close();
  }
});
await init();
