const REPO = "Stefan-Maximilian-Dietrich/PBG-Bot";
const BRANCH = "main";
const LOG_URL = `https://raw.githubusercontent.com/${REPO}/${BRANCH}/logs/checks.jsonl`;
const SNAPSHOT_BASE = `https://github.com/${REPO}/blob/${BRANCH}/`;
const MAX_ENTRIES = 200;

async function loadLogs() {
  const status = document.getElementById("status");
  const tbody = document.querySelector("#logTable tbody");
  const summary = document.getElementById("summary");
  status.textContent = "Lade…";
  status.className = "";

  try {
    const res = await fetch(LOG_URL + "?t=" + Date.now(), { cache: "no-store" });
    if (!res.ok) {
      if (res.status === 404) {
        tbody.innerHTML = `<tr><td colspan="5" class="empty">Noch keine Logs vorhanden. Warte auf den ersten Check.</td></tr>`;
        status.textContent = "Keine Logdatei gefunden.";
        return;
      }
      throw new Error("HTTP " + res.status);
    }

    const text = await res.text();
    const lines = text.trim().split("\n").filter(Boolean);
    const allEntries = lines.map((l) => {
      try { return JSON.parse(l); } catch { return null; }
    }).filter(Boolean);
    const entries = allEntries.slice().reverse().slice(0, MAX_ENTRIES);

    renderSummary(summary, allEntries);

    if (entries.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" class="empty">Logdatei ist leer.</td></tr>`;
    } else {
      tbody.innerHTML = entries.map(renderRow).join("");
    }

    status.textContent = `${entries.length} von ${allEntries.length} Einträgen, geladen ${new Date().toLocaleTimeString("de-DE")}`;
  } catch (err) {
    status.textContent = "Fehler: " + err.message;
    status.className = "err";
    tbody.innerHTML = `<tr><td colspan="5" class="empty">Konnte Logs nicht laden.</td></tr>`;
  }
}

function renderSummary(container, entries) {
  if (entries.length === 0) {
    container.innerHTML = "";
    return;
  }
  const total = entries.length;
  const changes = entries.filter((e) => e.result === "changed").length;
  const errors = entries.filter((e) => e.result === "error").length;
  const last = entries[entries.length - 1];
  const lastTime = last && last.timestamp ? last.timestamp : "—";
  container.innerHTML = `
    <div class="stat"><div class="label">Checks gesamt</div><div class="value">${total}</div></div>
    <div class="stat"><div class="label">Änderungen</div><div class="value">${changes}</div></div>
    <div class="stat"><div class="label">Fehler</div><div class="value">${errors}</div></div>
    <div class="stat"><div class="label">Letzter Check (UTC)</div><div class="value" style="font-size:0.95rem">${escapeHtml(lastTime)}</div></div>
  `;
}

function renderRow(e) {
  const cls = e.result || "";
  const hash = (e.hash || "").slice(0, 12);
  const details = renderDetails(e);
  return `
    <tr class="${escapeAttr(cls)}">
      <td><code>${escapeHtml(e.timestamp || "")}</code></td>
      <td>${escapeHtml(e.result || "")}</td>
      <td>${e.http_status ?? ""}</td>
      <td><code>${escapeHtml(hash)}</code></td>
      <td>${details}</td>
    </tr>
  `;
}

function renderDetails(e) {
  if (e.result === "error") {
    const count = e.error_count ? ` (Fehler ${e.error_count}x in Folge)` : "";
    return escapeHtml((e.error || "") + count);
  }
  if (e.result === "changed") {
    const prev = (e.previous_hash || "").slice(0, 12);
    const snapLink = e.snapshot
      ? ` · <a href="${SNAPSHOT_BASE}${encodeURI(e.snapshot)}" target="_blank" rel="noopener">Snapshot</a>`
      : "";
    return `vorher <code>${escapeHtml(prev)}</code>${snapLink}`;
  }
  return "";
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}

function escapeAttr(s) {
  return escapeHtml(s);
}

loadLogs();
setInterval(loadLogs, 60000);
