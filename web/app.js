const JERSEY_MS = 90 * 1000;
const CITIES_MS = 15 * 60 * 1000;

const els = {
  clock: document.getElementById("uk-clock"),
  lastRefresh: document.getElementById("last-refresh"),
  refreshBtn: document.getElementById("refresh-btn"),
  risk: document.getElementById("risk"),
  riskLevel: document.getElementById("risk-level"),
  riskSummary: document.getElementById("risk-summary"),
  cityGrid: document.getElementById("city-grid"),
  rugbyHero: document.getElementById("rugby-hero"),
  rugbyList: document.getElementById("rugby-list"),
};

function ukNow() {
  return new Date().toLocaleString("en-GB", {
    timeZone: "Europe/London",
    weekday: "short",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function formatStamp(iso) {
  if (!iso) return "Unknown time";
  return new Date(iso).toLocaleString("en-GB", {
    timeZone: "Europe/London",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function chipClass(status) {
  if (status === "ok") return "status-chip status-ok";
  if (status === "stale") return "status-chip status-stale";
  return "status-chip status-unavailable";
}

function setPanelStatus(panel, status) {
  const chip = panel.querySelector("[data-status]");
  chip.className = chipClass(status);
  chip.textContent = status === "ok" ? "Live" : status === "stale" ? "Stale" : "Unavailable";
}

function setFooter(panel, feed) {
  const foot = panel.querySelector(".panel-foot");
  const source = escapeHtml(feed.source || "Unknown source");
  const url = feed.sourceUrl || "#";
  foot.innerHTML = `${source} · Updated ${escapeHtml(formatStamp(feed.updatedAt))} · <a href="${escapeHtml(url)}" target="_blank" rel="noopener">Official source</a>`;
}

function unavailableHtml(feed, fallbackUrl) {
  const url = feed.sourceUrl || fallbackUrl;
  return `<p class="muted">Unavailable — <a href="${escapeHtml(url)}" target="_blank" rel="noopener">view official source</a></p>`;
}

function renderWeather(feed) {
  const panel = document.getElementById("panel-weather");
  setPanelStatus(panel, feed.status);
  setFooter(panel, feed);
  const body = panel.querySelector(".panel-body");
  if (!feed.data) {
    body.innerHTML = unavailableHtml(feed, "https://www.gov.je/weather/");
    return;
  }
  const fx = feed.data.forecast || {};
  const metar = feed.data.metar;
  const warning = feed.data.warning;
  const links = feed.data.links || {};
  body.innerHTML = `
    <p class="wx-now">${escapeHtml(fx.currentTemp || "—")}</p>
    <p>${escapeHtml(fx.summary || "No summary")}</p>
    <div class="wx-grid">
      <div>Max / min<br><strong>${escapeHtml(fx.maxTemp || "—")} / ${escapeHtml(fx.minTemp || "—")}</strong></div>
      <div>Wind<br><strong>${escapeHtml(fx.wind || "—")}</strong></div>
      <div>Rain chance<br><strong>${fx.rainChancePct != null ? `${escapeHtml(fx.rainChancePct)}%` : "—"}</strong></div>
      <div>UV<br><strong>${escapeHtml(fx.uvIndex || "—")}</strong></div>
    </div>
    ${warning ? `<p><strong>${escapeHtml(warning)}</strong></p>` : ""}
    ${metar?.raw ? `<p class="muted">METAR EGJJ: ${escapeHtml(metar.raw)}</p>` : ""}
    <p class="muted">
      <a href="${escapeHtml(links.warnings || "https://www.gov.je/weather/ciweatherwarnings/")}" target="_blank" rel="noopener">Warnings</a>
      · <a href="${escapeHtml(links.shipping || "https://www.gov.je/weather/shipping/")}" target="_blank" rel="noopener">Shipping</a>
      · <a href="${escapeHtml(links.tides || "https://www.gov.je/weather/tidetimes/")}" target="_blank" rel="noopener">Tides</a>
    </p>
  `;
}

function renderBoard(rows, columns, emptyNote) {
  if (!rows || !rows.length) {
    return `<p class="muted">${escapeHtml(emptyNote || "No movements on the current board.")}</p>`;
  }
  const head = columns.map((col) => `<th>${escapeHtml(col.label)}</th>`).join("");
  const body = rows
    .slice(0, 8)
    .map((row) => {
      const tds = columns
        .map((col) => `<td>${escapeHtml(row[col.key] || "—")}</td>`)
        .join("");
      return `<tr>${tds}</tr>`;
    })
    .join("");
  return `<table class="board"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}

function renderAirport(feed) {
  const panel = document.getElementById("panel-airport");
  setPanelStatus(panel, feed.status);
  setFooter(panel, feed);
  const body = panel.querySelector(".panel-body");
  if (!feed.data) {
    body.innerHTML = unavailableHtml(feed, "https://www.jerseyairport.com/flight/");
    return;
  }
  const cols = [
    { key: "scheduled", label: "Sched" },
    { key: "flight", label: "Flight" },
    { key: "location", label: "Route" },
    { key: "status", label: "Status" },
  ];
  body.innerHTML = `
    <h4>Arrivals</h4>
    ${renderBoard(feed.data.arrivals, cols, "No arrivals listed right now.")}
    <h4>Departures</h4>
    ${renderBoard(feed.data.departures, cols, "No departures listed right now.")}
    ${feed.data.boardUpdated ? `<p class="muted">Board stamp ${escapeHtml(feed.data.boardUpdated)}</p>` : ""}
  `;
}

function renderHarbour(feed) {
  const panel = document.getElementById("panel-harbour");
  setPanelStatus(panel, feed.status);
  setFooter(panel, feed);
  const body = panel.querySelector(".panel-body");
  if (!feed.data) {
    body.innerHTML = unavailableHtml(
      feed,
      "https://www.ports.je/jerseyharbours/arrivals-departures/"
    );
    return;
  }
  const arrivalCols = [
    { key: "vessel", label: "Vessel" },
    { key: "origin", label: "From" },
    { key: "status", label: "Status" },
  ];
  const departureCols = [
    { key: "vessel", label: "Vessel" },
    { key: "destination", label: "To" },
    { key: "status", label: "Status" },
  ];
  body.innerHTML = `
    <h4>Arrivals</h4>
    ${renderBoard(feed.data.arrivals, arrivalCols)}
    <h4>Departures</h4>
    ${renderBoard(feed.data.departures, departureCols)}
    <p class="muted">${escapeHtml(feed.data.note || "")}</p>
  `;
}

function renderDfds(feed) {
  const panel = document.getElementById("panel-dfds");
  setPanelStatus(panel, feed.status);
  setFooter(panel, feed);
  const body = panel.querySelector(".panel-body");
  if (!feed.data) {
    body.innerHTML = unavailableHtml(
      feed,
      "https://www.dfds.com/en-gb/passenger-ferries/passenger-information/travel-updates"
    );
    return;
  }
  const status = feed.data.sailingStatus || "unknown";
  const label =
    status === "cancelled"
      ? "Cancelled"
      : status === "delayed"
        ? "Delayed"
        : status === "updates"
          ? "Updates posted"
          : "Unknown";
  const chip =
    status === "cancelled"
      ? "sail-chip sail-cancelled"
      : status === "delayed"
        ? "sail-chip sail-delayed"
        : "sail-chip";
  const updates = (feed.data.updates || [])
    .map((item) => `<li>${escapeHtml(item)}</li>`)
    .join("");
  const fallback = (feed.data.fallbackRoutes || []).length
    ? `<p>Fallback routes to check: ${escapeHtml(feed.data.fallbackRoutes.join(", "))}</p>`
    : "";
  const links = feed.data.links || {};
  body.innerHTML = `
    <p><span class="${chip}">${label}</span> ${escapeHtml(feed.data.route)}</p>
    <ul class="updates">${updates || "<li class='muted'>No Jersey-specific update text found.</li>"}</ul>
    ${fallback}
    <p>
      <a href="${escapeHtml(links.updates || feed.sourceUrl)}" target="_blank" rel="noopener">DFDS travel updates</a>
      · <a href="${escapeHtml(links.route || "https://www.dfds.com/en-gb/passenger-ferries/ferry-crossings/ferries-to-jersey/st-malo-jersey")}" target="_blank" rel="noopener">St Malo–Jersey timetable</a>
    </p>
  `;
}

function renderRisk(risk) {
  const level = risk?.level || "pending";
  els.risk.className = `risk risk-${level}`;
  const words = { green: "Green", amber: "Amber", red: "Red", pending: "Loading" };
  els.riskLevel.textContent = words[level] || level;
  els.riskSummary.textContent = risk?.summary || "Risk not available.";
}

function renderCities(feed) {
  if (!feed?.data?.cities) {
    els.cityGrid.innerHTML = unavailableHtml(feed || {}, "https://open-meteo.com/");
    return;
  }
  els.cityGrid.innerHTML = feed.data.cities
    .map((city) => {
      const temp = city.temperatureC == null ? "—" : `${Math.round(city.temperatureC)}°C`;
      const high = city.highC == null ? "—" : `${Math.round(city.highC)}°`;
      const low = city.lowC == null ? "—" : `${Math.round(city.lowC)}°`;
      return `
        <article class="city-card">
          <h3>${escapeHtml(city.name)}</h3>
          <p class="city-temp">${escapeHtml(temp)}</p>
          <p>${escapeHtml(city.condition || "—")}</p>
          <p class="city-meta">Today ${escapeHtml(high)} / ${escapeHtml(low)} · Open-Meteo</p>
        </article>
      `;
    })
    .join("");
}

function countdownText(iso) {
  const target = new Date(iso).getTime();
  const diff = target - Date.now();
  if (diff <= 0) return "Kick-off has passed";
  const hours = Math.floor(diff / 3_600_000);
  const days = Math.floor(hours / 24);
  const remHours = hours % 24;
  const mins = Math.floor((diff % 3_600_000) / 60_000);
  if (days > 0) return `${days}d ${remHours}h ${mins}m`;
  return `${hours}h ${mins}m`;
}

function renderRugby(feed) {
  const next = feed?.data?.next;
  if (!next) {
    els.rugbyHero.innerHTML = `<p class="muted">No upcoming Springboks fixture in the curated list.</p>`;
    els.rugbyList.innerHTML = "";
    return;
  }
  els.rugbyHero.innerHTML = `
    <p class="hero-kicker">Next on TV</p>
    <h3 class="hero-title">${escapeHtml(next.home)} vs ${escapeHtml(next.away)}</h3>
    <p>${escapeHtml(next.round || "")} · ${escapeHtml(next.competition)}</p>
    <p>${escapeHtml(next.venue)}</p>
    <p class="countdown" data-kickoff="${escapeHtml(next.kickoffUtc)}">${escapeHtml(countdownText(next.kickoffUtc))}</p>
    <p><strong>Watch on ${escapeHtml(next.watchOn || next.ukBroadcaster)}</strong>
      ${(next.ukStream || []).length ? ` · ${escapeHtml(next.ukStream.join(" / "))}` : ""}</p>
    <p>${escapeHtml(next.kickoffUk)}</p>
    ${next.broadcastNote ? `<p class="muted">${escapeHtml(next.broadcastNote)}</p>` : ""}
  `;
  els.rugbyList.innerHTML = (feed.data.fixtures || [])
    .map((fix) => {
      return `
        <li class="${fix.played ? "played" : ""}">
          <strong>${escapeHtml(fix.home)} vs ${escapeHtml(fix.away)}</strong>
          <span>${escapeHtml(fix.kickoffUk)} · ${escapeHtml(fix.venue)}</span>
          <span>Watch on ${escapeHtml(fix.watchOn || "TBC")}${fix.played ? " · Played" : ""}</span>
        </li>
      `;
    })
    .join("");
}

function tickCountdown() {
  const node = document.querySelector("[data-kickoff]");
  if (!node) return;
  node.textContent = countdownText(node.getAttribute("data-kickoff"));
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${url} ${response.status}`);
  return response.json();
}

async function loadJersey() {
  try {
    const data = await fetchJson("/api/jersey");
    renderRisk(data.risk);
    renderWeather(data.weather);
    renderAirport(data.airport);
    renderHarbour(data.harbour);
    renderDfds(data.dfds);
  } catch (err) {
    renderRisk({
      level: "amber",
      summary: "Could not reach the Jersey aggregator. Retrying.",
    });
    console.error(err);
  }
}

async function loadCities() {
  try {
    renderCities(await fetchJson("/api/cities"));
  } catch (err) {
    els.cityGrid.innerHTML = `<p class="muted">City forecasts unavailable.</p>`;
    console.error(err);
  }
}

async function loadRugby() {
  try {
    renderRugby(await fetchJson("/api/springboks"));
  } catch (err) {
    els.rugbyHero.innerHTML = `<p class="muted">Fixtures unavailable.</p>`;
    console.error(err);
  }
}

async function refreshAll() {
  els.lastRefresh.textContent = `Refreshing…`;
  await Promise.all([loadJersey(), loadCities(), loadRugby()]);
  els.lastRefresh.textContent = `Last refresh ${ukNow()}`;
}

els.refreshBtn.addEventListener("click", () => {
  refreshAll();
});

setInterval(() => {
  els.clock.textContent = `UK time ${ukNow()}`;
}, 1000);
els.clock.textContent = `UK time ${ukNow()}`;

setInterval(tickCountdown, 30_000);
setInterval(loadJersey, JERSEY_MS);
setInterval(loadCities, CITIES_MS);

refreshAll();
