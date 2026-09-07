const config = new URLSearchParams(location.search);
const api = (config.get("api") || localStorage.getItem("arriva-api") || "http://127.0.0.1:8000").replace(/\/$/, "");
const wsBase = api.replace(/^http/, "ws");
const state = { trains: [], selected: null, eta: null };
const $ = id => document.getElementById(id);
const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function renderList() {
  const term = $("search").value.toLowerCase();
  const visible = state.trains.filter(t => [t.train_id,t.train_number,t.train_name,t.origin,t.destination,t.current_station,t.next_station].join(" ").toLowerCase().includes(term));
  $("trains").innerHTML = visible.length ? visible.map(t => `<article class="train ${state.selected===t.train_id?"selected":""}" data-id="${esc(t.train_id)}"><div class="train-top"><strong>${esc(t.train_name)} <span class="muted">#${esc(t.train_number)}</span></strong><span class="status">${esc(t.status)}</span></div><p class="sub">${esc(t.origin)} → ${esc(t.destination)} · at ${esc(t.current_station)}</p><p class="sub">${esc(t.next_station || "Destination")} · ${Number(t.current_delay_minutes || 0).toFixed(1)} min delay</p></article>`).join("") : '<p class="muted">No trains match that search.</p>';
  document.querySelectorAll(".train").forEach(el => el.onclick = () => select(el.dataset.id));
}
async function select(id) {
  state.selected = id; renderList(); $("details").className = "details"; $("details").innerHTML = "<p class=muted>Loading live ETA…</p>";
  try { const r = await fetch(`${api}/api/trains/${encodeURIComponent(id)}/eta`); if (!r.ok) throw Error(); state.eta = await r.json(); renderDetails(); } catch { $("details").innerHTML = "<p class=muted>ETA unavailable. Check the API connection.</p>"; }
}
function renderDetails() {
  const t = state.trains.find(x => x.train_id === state.selected), e = state.eta;
  if (!t || !e) return;
  const stations = (e.upcoming_station_etas || []).slice(0, 4).map(x => `<li>${esc(x.station)} — ${new Date(x.predicted_arrival).toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"})}</li>`).join("");
  $("details").innerHTML = `<div class=train-top><div><h2>${esc(t.train_name)}</h2><p class=sub>${esc(t.train_id)} · ${esc(t.origin)} → ${esc(t.destination)}</p></div><span class=status>${esc(e.risk_level)} risk</span></div><div class=metrics><div class=metric>ETA<b>${new Date(e.predicted_arrival).toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"})}</b></div><div class=metric>Delay<b>${Number(e.predicted_delay_minutes).toFixed(1)} min</b></div><div class=metric>Next station<b>${esc(t.next_station || "Arrived")}</b></div><div class=metric>Distance<b>${Number(t.distance_remaining_km).toFixed(1)} km</b></div></div><h3>Upcoming stations</h3><ol class=stations>${stations || "<li>No upcoming stops</li>"}</ol>`;
}
async function load() { try { const r = await fetch(`${api}/api/trains`); if (!r.ok) throw Error(); state.trains = await r.json(); $("connection").textContent = "REST online"; $("connection").className = "pill online"; renderList(); } catch { $("connection").textContent = "Offline"; $("connection").className = "pill offline"; $("trains").innerHTML = '<p class=muted>Could not reach ARRIVA API.</p>'; } }
function connect() {
  const ws = new WebSocket(`${wsBase}/ws/trains?interval_seconds=2&advance_minutes=2`);
  ws.onopen = () => { $("connection").textContent = "Live"; $("connection").className = "pill online"; };
  ws.onmessage = event => { const u = JSON.parse(event.data), t = state.trains.find(x => x.train_id === u.train_id); if (t) Object.assign(t, {latitude:u.latitude,longitude:u.longitude,current_delay_minutes:u.current_delay,distance_remaining_km:u.distance_remaining,next_station:u.next_station,status:u.current_delay > 3 ? "running_late" : "running"}); renderList(); if (state.selected === u.train_id) { state.eta = Object.assign(state.eta || {}, {predicted_delay_minutes:u.predicted_delay,predicted_arrival:u.predicted_arrival,risk_level:u.delay_risk}); renderDetails(); } };
  ws.onclose = () => { $("connection").textContent = "Reconnecting"; $("connection").className = "pill offline"; setTimeout(connect, 3000); };
}
$("search").oninput = renderList;
load(); connect();
if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js");
