
(() => {
  const STATUSES = [
    ["planning", "Planning"], ["recorded", "Recorded"], ["editing", "Editing"],
    ["review", "Awaiting approval"], ["approved", "Approved, publishing"], ["published", "Published"]
  ];
  const CLIP_STATUSES = [["idea", "Idea"], ["cut", "Cut"], ["posted", "Posted"]];
  const S = {
    me: null, canWrite: false, episodes: [], ideas: [], loaded: false, slow: false, error: null,
    view: "episodes", openId: null, tab: "prep", editing: null, confirmDel: null, newEp: false,
    pending: false, prompter: null, scale: 1
  };
  const $app = document.getElementById("app");
  const $prompter = document.getElementById("prompter");

  // ---------- helpers ----------
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const uid = () => Math.random().toString(36).slice(2, 10);
  const todayISO = () => { const d = new Date(); return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10); };
  const fmtDate = iso => { if (!iso) return ""; const [y, m, d] = iso.split("-").map(Number); return new Date(Date.UTC(y, m - 1, d)).toLocaleDateString(undefined, { timeZone: "UTC", weekday: "short", month: "short", day: "numeric", year: "numeric" }); };
  const statusLabel = (list, v) => (list.find(s => s[0] === v) || [v, v])[1];
  function inline(s) {
    return s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/(^|[^*\w])\*([^*\n]+?)\*(?=[^*\w]|$)/g, "$1<em>$2</em>")
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/(https?:\/\/[^\s<)]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>');
  }
  function rich(text) {
    const lines = esc(text || "").split("\n");
    let out = "", list = null, para = [];
    const flushP = () => { if (para.length) { out += "<p>" + inline(para.join("<br>")) + "</p>"; para = []; } };
    const flushL = () => { if (list) { out += `<${list.t}>` + list.items.map(i => "<li>" + inline(i) + "</li>").join("") + `</${list.t}>`; list = null; } };
    for (const raw of lines) {
      const l = raw.trimEnd();
      let m;
      if (!l.trim()) { flushP(); flushL(); continue; }
      if ((m = l.match(/^\s*[-*]\s+(.*)$/))) { flushP(); if (!list || list.t !== "ul") { flushL(); list = { t: "ul", items: [] }; } list.items.push(m[1]); continue; }
      if ((m = l.match(/^\s*\d+\.\s+(.*)$/))) { flushP(); if (!list || list.t !== "ol") { flushL(); list = { t: "ol", items: [] }; } list.items.push(m[1]); continue; }
      if ((m = l.match(/^&gt;\s?(.*)$/))) { flushP(); flushL(); out += "<blockquote>" + inline(m[1]) + "</blockquote>"; continue; }
      if ((m = l.match(/^#{2,4}\s+(.*)$/))) { flushP(); flushL(); out += "<h4>" + inline(m[1]) + "</h4>"; continue; }
      if (list && /^\s{2,}/.test(raw)) { list.items[list.items.length - 1] += " " + l.trim(); continue; }
      flushL(); para.push(l);
    }
    flushP(); flushL();
    return out;
  }
  let toastT;
  function toast(msg) { const t = document.getElementById("toast"); t.textContent = msg; t.hidden = false; clearTimeout(toastT); toastT = setTimeout(() => t.hidden = true, 2600); }

  async function api(path, method = "GET", body) {
    const response = await fetch("/api/" + path, {method, headers: {
      "Content-Type": "application/json", "X-Peak-Mind-Studio": "1"
    }, body: body === undefined ? undefined : JSON.stringify(body)});
    const data = await response.json();
    if (!response.ok) {
      if (data.episode) replaceDoc("episodes", data.episode);
      throw new Error(data.error || "Request failed");
    }
    return data;
  }
  function replaceDoc(collection, doc) {
    const index = S[collection].findIndex(x => x.id === doc.id);
    if (index < 0) S[collection].push(doc); else S[collection][index] = doc;
  }
  const queues = {};
  function write(path, fn, okMsg) {
    const [collection, id] = path.split("/");
    const run = async () => {
      const current = S[collection].find(x => x.id === id);
      const send = async (method, fields = {}) => {
        const doc = await api(path, method, {...fields, ifVersion: current?.version});
        if (method === "DELETE") S[collection] = S[collection].filter(x => x.id !== id);
        else replaceDoc(collection, doc);
      };
      await fn({update: fields => send("PATCH", fields), set: fields => send("PUT", fields), delete: () => send("DELETE")});
      S.error = null;
      if (okMsg) toast(okMsg);
      render();
    };
    const promise = (queues[path] || Promise.resolve()).catch(() => {}).then(run);
    queues[path] = promise;
    promise.catch(error => { toast(error.message); S.error = error.message; render(); });
    return promise;
  }
  const ep = () => S.episodes.find(e => e.id === S.openId);
  function patchEp(fields, msg) {
    const e = ep(); if (!e) return Promise.resolve();
    return write("episodes/" + e.id, ref => ref.update(fields), msg);
  }

  // ---------- routing ----------
  function defaultEpisodeId() {
    const t = todayISO();
    const upcoming = S.episodes.filter(e => e.date >= t).sort((a, b) => a.date.localeCompare(b.date));
    return (upcoming[0] || S.episodes[0] || {}).id || null;
  }
  function readHash() {
    S.editing = null; S.confirmDel = null; S.newEp = false;
    let h; try { h = decodeURIComponent(location.hash.slice(1)); } catch (_) { h = "episodes"; }
    if (h === "ideas") { S.view = "ideas"; }
    else if (h.startsWith("ep-")) { S.view = "episodes"; if (S.openId !== h.slice(3)) { S.openId = h.slice(3); S.tab = S.episodes.find(e => e.id === S.openId)?.status === "review" ? "review" : "prep"; S.editing = null; } }
    else { S.view = "episodes"; S.openId = null; }
  }
  window.addEventListener("hashchange", () => { readHash(); render(true); window.scrollTo(0, 0); });

  // ---------- rendering ----------
  function render(force) {
    document.getElementById("nav-episodes").setAttribute("aria-current", S.view === "episodes" ? "page" : "false");
    document.getElementById("nav-ideas").setAttribute("aria-current", S.view === "ideas" ? "page" : "false");
    if (S.editing && !force) { S.pending = true; renderRailOnly(); return; }
    S.pending = false;
    if (S.error && !S.loaded) { $app.innerHTML = `<div class="empty"><h2>Your notes couldn't load</h2><p>Reload the page to try again.</p></div>`; return; }
    if (!S.loaded) { $app.innerHTML = `<div class="empty"><h2>Loading your episodes</h2><p>${S.slow ? "This is taking longer than usual. Check your connection; the page keeps trying." : "Your prep notes, scripts and clips will appear here."}</p></div>`; return; }
    // keep whatever is being typed in the quick-add boxes across live updates
    const keep = {}; let focusId = null, sel = null;
    for (const id of ["new-check", "new-idea", "ne-title", "ne-date"]) { const el = document.getElementById(id); if (el) keep[id] = el.value; }
    const act = document.activeElement;
    if (act && act.id && $app.contains(act)) { focusId = act.id; try { sel = act.selectionStart; } catch (_) {} }
    $app.innerHTML = S.view === "ideas" ? ideasView() : episodesView();
    for (const id in keep) { const el = document.getElementById(id); if (el && force !== "clear") el.value = keep[id]; }
    if (focusId) { const el = document.getElementById(focusId); if (el) { el.focus(); try { if (sel != null) el.setSelectionRange(sel, sel); } catch (_) {} return; } }
    afterRender();
  }
  function renderRailOnly() { const r = document.getElementById("rail"); if (r) r.innerHTML = railInner(); }
  function afterRender() {
    const f = $app.querySelector("[data-autofocus]"); if (f) f.focus();
  }

  function banner() {
    let b = "";
    if (S.canWrite === false) b += `<div class="banner">You can read this page but not edit it.</div>`;
    if (S.error) b += `<div class="banner" role="alert">${esc(S.error)}</div>`;
    if (S.slow && S.loaded) b += `<div class="banner">Can't reach storage right now. What you see may be out of date.</div>`;
    return b;
  }

  function railInner() {
    const t = todayISO();
    const list = [...S.episodes].sort((a, b) => b.date.localeCompare(a.date));
    return `<div class="rail-head"><span class="label">Episodes</span>${S.canWrite !== false ? `<button class="btn sm" data-act="new-ep">+ New</button>` : ""}</div>
      ${S.newEp ? newEpForm() : ""}
      ${list.length ? list.map(e => `<a class="ep-item" href="#ep-${esc(e.id)}" aria-current="${e.id === S.openId}">
        <span class="row"><span class="ep-date">${esc(fmtDate(e.date))}</span>${pill(e, t)}</span>
        <span class="ep-title">${esc(e.title || "Untitled episode")}</span></a>`).join("")
      : `<div class="empty"><p>No episodes yet. Use + New to add tonight's show.</p></div>`}`;
  }
  function pill(e, t) {
    if (e.date === t && (e.status === "planning" || !e.status)) return `<span class="pill st-live">Tonight</span>`;
    return `<span class="pill st-${esc(e.status || "planning")}">${esc(statusLabel(STATUSES, e.status || "planning"))}</span>`;
  }
  function newEpForm() {
    return `<form class="card form" data-form="new-ep">
      <label>Recording date<input type="date" id="ne-date" required value="${todayISO()}"></label>
      <label>Title<input id="ne-title" placeholder="Working title" required data-autofocus></label>
      <div class="actions"><button class="btn primary" type="submit">Add episode</button><button class="btn ghost" type="button" data-act="cancel-new">Cancel</button></div>
    </form>`;
  }

  function episodesView() {
    if (!S.openId && window.matchMedia("(min-width: 861px)").matches) { S.openId = defaultEpisodeId(); S.tab = ep()?.status === "review" ? "review" : "prep"; }
    const e = ep();
    return `${banner()}<div class="desk ${e ? "has-open" : ""}">
      <aside class="rail" id="rail">${railInner()}</aside>
      <section class="main">${e ? episodeDetail(e) : `<div class="empty"><h2>Pick an episode</h2><p>Choose one from the list to see its prep, script and clips.</p></div>`}</section>
    </div>`;
  }

  function episodeDetail(e) {
    const editingHead = S.editing === "head";
    const links = [["spaceUrl", "X Space"], ["promoUrl", "Promo post"], ["spotifyUrl", "Spotify"]].filter(([k]) => e[k]);
    if (!e.review && e.status !== "review" && S.tab === "review") S.tab = "prep";
    const counts = { prep: (e.sections || []).length, script: (e.beats || []).length, clips: (e.clips || []).length };
    const w = S.canWrite !== false;
    return `<a class="btn ghost sm back" href="#episodes">← All episodes</a>
    ${editingHead ? headForm(e) : `<div class="head">
      <div class="head-top"><span class="ep-date">${esc(fmtDate(e.date))}${e.time ? " · " + esc(e.time) : ""}</span>${pill(e, todayISO())}
        ${w ? `<button class="btn ghost sm" data-act="edit-head">Edit details</button>` : ""}</div>
      <h1>${esc(e.title || "Untitled episode")}</h1>
      ${e.summary ? `<p class="summary">${esc(e.summary)}</p>` : ""}
      ${links.length ? `<div class="links">${links.map(([k, l]) => `<a class="btn sm" href="${esc(e[k])}" target="_blank" rel="noopener">${l} ↗</a>`).join("")}</div>` : ""}
    </div>`}
    <div class="tabs" role="tablist">
      ${[...(e.review || e.status === "review" ? [["review", "Review"]] : []), ["prep", "Prep"], ["script", "Script"], ["clips", "Clips"]].map(([k, l]) => `<button class="tab" role="tab" aria-selected="${S.tab === k}" data-act="tab" data-tab="${k}">${l}<span class="n">${counts[k] || ""}</span></button>`).join("")}
    </div>
    ${S.tab === "review" ? reviewTab(e) : S.tab === "prep" ? prepTab(e) : S.tab === "script" ? scriptTab(e) : clipsTab(e)}`;
  }

  function mediaUrl(value) { return "/media/" + String(value).split("/").map(encodeURIComponent).join("/"); }
  function reviewTab(e) {
    const r = e.review, a = e.approval;
    if (!r) return `<div class="empty"><h2>Waiting for the weekly review</h2><p>The episode is awaiting approval. Its title, cuts, covers and listening clips will appear here when the weekly run writes the review.</p></div>`;
    const decision = a ? `<div class="card decision" role="status"><h3>${a.decision === "approved" ? "Approval recorded" : "Changes requested"}</h3>
      <p>${esc(a.name)} (${esc(a.by)}) at ${esc(a.at)}${a.cover ? `, cover ${esc(a.cover)}` : ""}</p>
      ${a.note ? `<p>${esc(a.note)}</p>` : ""}
      <p><strong>${a.delivered ? "Delivered to the publishing thread" : "Not delivered to the publishing thread"}</strong></p>
      ${a.deliveryError ? `<p class="banner">${esc(a.deliveryError)}. Retry below or reply in T3.</p>` : ""}</div>` : "";
    const canDecide = S.me?.canApprove && e.status === "review";
    return `<div class="stack">${decision}
      <article class="card"><h2>${esc(r.title)}</h2>
        <h3 class="review-heading">Title alternates</h3><ul>${r.titleAlternates.map(x => `<li>${esc(x)}</li>`).join("")}</ul>
        <h3>Short description <small class="meta">${r.conciseDescription.length} characters</small></h3><p class="review-copy">${esc(r.conciseDescription)}</p>
        <h3>Spotify description <small class="meta">${r.spotifyDescription.trim().split(/\s+/).filter(Boolean).length} words</small></h3><p class="review-copy">${esc(r.spotifyDescription)}</p>
        <p><strong>Length:</strong> ${esc(r.length)} · <strong>Confidence:</strong> ${esc(r.confidence)}</p>
        ${r.confidenceNote ? `<p>${esc(r.confidenceNote)}</p>` : ""}</article>
      <div class="review-cuts"><article class="card"><h3>Start cut: ${esc(r.start.at)}</h3><p>Cut: <q>${esc(r.start.cutLine)}</q></p><p>First line: <q>${esc(r.start.firstLine)}</q></p></article>
        <article class="card"><h3>End cut: ${esc(r.end.at)}</h3><p>Last line: <q>${esc(r.end.lastLine)}</q></p><p>Cut: <q>${esc(r.end.cutLine)}</q></p></article></div>
      <article class="card"><h3>Flags</h3>${r.flags.length ? `<ul>${r.flags.map(x => `<li>${esc(x)}</li>`).join("")}</ul>` : `<p>No flags reported.</p>`}</article>
      <form class="stack" data-form="decision">
        <fieldset class="card"><legend>Cover options</legend><div class="review-covers">${r.covers.map(c => `<label class="cover-option"><img src="${mediaUrl(c.media)}" alt="${esc(c.label)}" loading="lazy"><span><input type="radio" name="cover" value="${esc(c.id)}" ${c.id === (a?.cover || r.defaultCover) ? "checked" : ""} ${canDecide ? "" : "disabled"}> ${esc(c.label)}</span></label>`).join("")}</div></fieldset>
        <section class="card"><h3>Listening clips</h3>${r.clips.map(c => `<label class="review-audio">${esc(c.label)}<audio controls preload="none" src="${mediaUrl(c.media)}"></audio></label>`).join("")}</section>
        ${canDecide ? `<div class="card form"><label>Note (required for changes)<textarea id="decision-note" name="note" style="min-height:100px" maxlength="10000"></textarea></label>
          <div class="actions"><button class="btn primary" type="submit" name="decision" value="approve">Approve and publish</button><button class="btn" type="submit" name="decision" value="request-changes">Request changes</button></div>
          <p id="decision-error" class="hint" role="alert"></p></div>` : `<p class="hint">${e.status === "approved" ? "Approved, publishing. The weekly run will mark it published." : "Approval requires a configured person signed in through the tailnet."}</p>`}
      </form></div>`;
  }

  function headForm(e) {
    return `<form class="card form" data-form="head" style="margin-bottom:16px">
      <label>Title<input id="h-title" value="${esc(e.title)}" data-autofocus></label>
      <div class="grid2">
        <label>Time<input id="h-time" value="${esc(e.time)}" placeholder="7:00 PM ET"></label>
        <label>Status<select id="h-status">${STATUSES.filter(([v]) => v !== "approved" || e.status === "approved").map(([v, l]) => `<option value="${v}" ${e.status === v ? "selected" : ""}>${l}</option>`).join("")}</select></label>
      </div>
      <label>One-line description<textarea id="h-summary" style="min-height:70px">${esc(e.summary)}</textarea></label>
      <div class="grid2">
        <label>X Space link<input id="h-space" value="${esc(e.spaceUrl)}" placeholder="https://x.com/i/spaces/…"></label>
        <label>Promo post link<input id="h-promo" value="${esc(e.promoUrl)}"></label>
        <label>Spotify link<input id="h-spotify" value="${esc(e.spotifyUrl)}"></label>
      </div>
      <div class="actions"><button class="btn primary" type="submit">Save</button><button class="btn ghost" type="button" data-act="cancel-edit">Cancel</button>
        <span class="spacer" style="flex:1"></span>
        ${S.confirmDel === "episode" ? `<span class="hint">Delete this episode and everything in it?</span><button class="btn danger sm" type="button" data-act="del-episode">Delete</button><button class="btn ghost sm" type="button" data-act="no-del">Keep</button>` : `<button class="btn ghost sm danger" type="button" data-act="ask-del" data-what="episode">Delete episode</button>`}
      </div>
    </form>`;
  }

  // ----- Prep tab -----
  function prepTab(e) {
    const w = S.canWrite !== false;
    const checklist = e.checklist || [];
    return `<div class="stack">
      <div class="card">
        <div class="card-head"><h3>Before and during the show</h3></div>
        <div class="checklist" style="margin-top:8px">
          ${checklist.map(c => `<label class="check ${c.done ? "done" : ""}"><input type="checkbox" data-act="toggle-check" data-id="${c.id}" ${c.done ? "checked" : ""} ${w ? "" : "disabled"}><span>${inline(esc(c.text))}</span>
            ${w ? `<button class="btn ghost sm" type="button" data-act="del-check" data-id="${c.id}" aria-label="Remove item">✕</button>` : ""}</label>`).join("") || `<p class="hint">Nothing on the checklist yet.</p>`}
        </div>
        ${w ? `<form class="idea-add" data-form="add-check" style="margin:10px 0 0"><input id="new-check" placeholder="Add a checklist item"><button class="btn" type="submit">Add</button></form>` : ""}
      </div>
      ${(e.sections || []).map((s, i, arr) => S.editing === "sec:" + s.id ? sectionForm(s) : `
        <details class="card" ${s.collapsed ? "" : "open"} data-sec="${s.id}">
          <summary class="card-head"><h3>${esc(s.heading)}</h3>
            ${w ? `<span class="card-tools">
              <button class="btn ghost sm" data-act="move" data-list="sections" data-id="${s.id}" data-dir="-1" ${i === 0 ? "disabled" : ""} aria-label="Move up">↑</button>
              <button class="btn ghost sm" data-act="move" data-list="sections" data-id="${s.id}" data-dir="1" ${i === arr.length - 1 ? "disabled" : ""} aria-label="Move down">↓</button>
              <button class="btn ghost sm" data-act="edit" data-key="sec:${s.id}">Edit</button></span>` : ""}
          </summary>
          <div class="rich">${rich(s.body)}</div>
        </details>`).join("")}
      ${S.editing === "sec:new" ? sectionForm({ id: "new", heading: "", body: "" }) : w ? `<div><button class="btn" data-act="edit" data-key="sec:new">+ Add a section</button></div>` : ""}
    </div>`;
  }
  function formatHint() { return `<span class="hint">Formatting: start a line with "- " for a bullet or "1. " for a numbered step. Wrap words in **double stars** for bold.</span>`; }
  function sectionForm(s) {
    return `<form class="card form" data-form="section" data-id="${s.id}">
      <label>Heading<input id="f-heading" value="${esc(s.heading)}" required data-autofocus></label>
      <label>Notes<textarea id="f-body" style="min-height:260px">${esc(s.body)}</textarea>${formatHint()}</label>
      ${formActions(s.id !== "new", "section")}
    </form>`;
  }
  function formActions(canDelete, what) {
    return `<div class="actions"><button class="btn primary" type="submit">Save</button><button class="btn ghost" type="button" data-act="cancel-edit">Cancel</button>
      <span style="flex:1"></span>
      ${!canDelete ? "" : S.confirmDel === what ? `<span class="hint">Delete this ${what}?</span><button class="btn danger sm" type="button" data-act="del-item">Delete</button><button class="btn ghost sm" type="button" data-act="no-del">Keep</button>` : `<button class="btn ghost sm danger" type="button" data-act="ask-del" data-what="${what}">Delete</button>`}
    </div>`;
  }

  // ----- Script tab -----
  function scriptTab(e) {
    const w = S.canWrite !== false;
    const beats = e.beats || [];
    return `<div class="toolbar">
        ${beats.length ? `<button class="btn primary" data-act="prompter" data-idx="0">Read on air</button>` : ""}
        <span class="hint">Big text, one beat at a time. Use the arrow keys or the buttons to move.</span>
      </div>
      <div class="stack">
      ${S.editing === "note" ? `<form class="card form" data-form="note"><label>How to read it<textarea id="f-note" data-autofocus>${esc(e.scriptNote)}</textarea>${formatHint()}</label>${formActions(false)}</form>`
        : e.scriptNote ? `<details class="card"><summary class="card-head"><h3>How to read it</h3>${w ? `<span class="card-tools"><button class="btn ghost sm" data-act="edit" data-key="note">Edit</button></span>` : ""}</summary><div class="rich">${rich(e.scriptNote)}</div></details>` : ""}
      ${beats.map((b, i, arr) => S.editing === "beat:" + b.id ? beatForm(b) : `
        <article class="card">
          <div class="card-head"><div><div class="beat-kicker">${esc(b.kicker || "Beat " + (i + 1))}</div><h3>${esc(b.title)}</h3></div>
            <span class="card-tools">
              <button class="btn ghost sm" data-act="prompter" data-idx="${i}">Read</button>
              ${w ? `<button class="btn ghost sm" data-act="move" data-list="beats" data-id="${b.id}" data-dir="-1" ${i === 0 ? "disabled" : ""} aria-label="Move up">↑</button>
              <button class="btn ghost sm" data-act="move" data-list="beats" data-id="${b.id}" data-dir="1" ${i === arr.length - 1 ? "disabled" : ""} aria-label="Move down">↓</button>
              <button class="btn ghost sm" data-act="edit" data-key="beat:${b.id}">Edit</button>` : ""}
            </span></div>
          ${b.hook ? `<p class="hook">${esc(b.hook)}</p>` : ""}
          <div class="rich">${rich(b.body)}</div>
          ${b.handoff ? `<div class="handoff"><b>→ JT</b> ${inline(esc(b.handoff))}</div>` : ""}
        </article>`).join("")}
      ${S.editing === "beat:new" ? beatForm({ id: "new", kicker: "", title: "", hook: "", body: "", handoff: "" }) : w ? `<div><button class="btn" data-act="edit" data-key="beat:new">+ Add a beat</button></div>` : ""}
    </div>`;
  }
  function beatForm(b) {
    return `<form class="card form" data-form="beat" data-id="${b.id}">
      <div class="grid2"><label>Label<input id="b-kicker" value="${esc(b.kicker)}" placeholder="Beat 4"></label><label>Title<input id="b-title" value="${esc(b.title)}" required data-autofocus></label></div>
      <label>Hook line<input id="b-hook" value="${esc(b.hook)}"><span class="hint">The first words you say. Clips start here.</span></label>
      <label>Script<textarea id="b-body" style="min-height:280px">${esc(b.body)}</textarea>${formatHint()}</label>
      <label>Handoff to JT<input id="b-handoff" value="${esc(b.handoff)}" placeholder="Optional question for JT"></label>
      ${formActions(b.id !== "new", "beat")}
    </form>`;
  }

  // ----- Clips tab -----
  function clipsTab(e) {
    const w = S.canWrite !== false;
    const clips = e.clips || [];
    const editingClip = S.editing && S.editing.startsWith("clip:") ? S.editing.slice(5) : null;
    return `<div class="toolbar"><span class="hint">Clip ideas from this episode. Each clip starts on its hook line.</span><span class="spacer"></span>
        ${w && editingClip !== "new" ? `<button class="btn" data-act="edit" data-key="clip:new">+ Add a clip</button>` : ""}</div>
      ${editingClip === "new" ? clipForm({ id: "new", status: "idea" }) : ""}
      ${clips.length ? `<div class="clips">${clips.map(c => editingClip === c.id ? clipForm(c) : `
        <article class="card clip">
          <div class="card-head"><span class="pill st-${esc(c.status || "idea")}">${esc(statusLabel(CLIP_STATUSES, c.status || "idea"))}</span>
            ${w ? `<span class="card-tools"><button class="btn ghost sm" data-act="edit" data-key="clip:${c.id}">Edit</button></span>` : ""}</div>
          <h3 style="margin-top:8px">${esc(c.title)}</h3>
          ${c.hook ? `<p class="q">Starts: “${esc(c.hook)}”</p>` : ""}
          ${c.ends ? `<p class="hint" style="margin:0 0 6px">Ends: ${esc(c.ends)}</p>` : ""}
          ${(c.start || c.end) ? `<p class="meta">${esc(c.start || "?")} → ${esc(c.end || "?")}</p>` : ""}
          ${c.note ? `<div class="rich">${rich(c.note)}</div>` : ""}
          ${c.link ? `<a class="btn sm" href="${esc(c.link)}" target="_blank" rel="noopener">Open ↗</a>` : ""}
        </article>`).join("")}</div>` : editingClip ? "" : `<div class="empty"><p>No clips yet. After the show, add the moments worth posting.</p></div>`}`;
  }
  function clipForm(c) {
    return `<form class="card form" data-form="clip" data-id="${c.id}" style="margin-bottom:12px">
      <div class="grid2"><label>Title<input id="c-title" value="${esc(c.title)}" required data-autofocus></label>
        <label>Status<select id="c-status">${CLIP_STATUSES.filter(([v]) => v !== "approved" || e.status === "approved").map(([v, l]) => `<option value="${v}" ${c.status === v ? "selected" : ""}>${l}</option>`).join("")}</select></label></div>
      <label>Starts on (hook line)<input id="c-hook" value="${esc(c.hook)}"></label>
      <label>Ends on<input id="c-ends" value="${esc(c.ends)}"></label>
      <div class="grid2"><label>Start time<input id="c-start" value="${esc(c.start)}" placeholder="1:02:15"></label><label>End time<input id="c-end" value="${esc(c.end)}" placeholder="1:03:40"></label></div>
      <label>Notes<textarea id="c-note" style="min-height:90px">${esc(c.note)}</textarea></label>
      <label>Link to posted clip<input id="c-link" value="${esc(c.link)}"></label>
      ${formActions(c.id !== "new", "clip")}
    </form>`;
  }

  // ----- Ideas -----
  function ideasView() {
    const w = S.canWrite !== false;
    const open = S.ideas.filter(i => !i.used), used = S.ideas.filter(i => i.used);
    const row = i => `<div class="card idea ${i.used ? "used" : ""}">
      <div class="txt">${S.editing === "idea:" + i.id ? `<form class="form" data-form="idea" data-id="${i.id}"><textarea id="i-text" style="min-height:80px" data-autofocus>${esc(i.text)}</textarea>${formActions(true, "idea")}</form>` : `<div class="rich" style="margin-top:-10px">${rich(i.text)}</div><span class="meta">${i.createdAt ? esc(new Date(i.createdAt).toLocaleDateString()) : ""}</span>`}</div>
      ${w && S.editing !== "idea:" + i.id ? `<span class="card-tools"><button class="btn ghost sm" data-act="toggle-idea" data-id="${i.id}">${i.used ? "Reopen" : "Mark used"}</button><button class="btn ghost sm" data-act="edit" data-key="idea:${i.id}">Edit</button></span>` : ""}
    </div>`;
    return `${banner()}<div style="max-width:820px">
      <div class="head"><h1>Topic ideas</h1><p class="summary">Things to cover on a future Peak Mind. Mark one used once it's been on the show.</p></div>
      ${w ? `<form class="idea-add" data-form="add-idea"><input id="new-idea" placeholder="A topic, a link, a question for JT"><button class="btn primary" type="submit">Add</button></form>` : ""}
      <div class="stack">${open.length ? open.map(row).join("") : `<div class="empty"><p>No open ideas. Add the next thing you want to talk about.</p></div>`}</div>
      ${used.length ? `<p class="label" style="margin:24px 0 8px">Already covered</p><div class="stack">${used.map(row).join("")}</div>` : ""}
    </div>`;
  }

  // ---------- prompter ----------
  let wake = null;
  function openPrompter(idx) {
    S.prompter = idx; renderPrompter(); $prompter.hidden = false; document.body.style.overflow = "hidden";
    try { navigator.wakeLock?.request("screen").then(l => wake = l).catch(() => {}); } catch (_) {}
  }
  function closePrompter() {
    S.prompter = null; $prompter.hidden = true; document.body.style.overflow = "";
    try { wake?.release(); } catch (_) {} wake = null;
  }
  function renderPrompter() {
    const e = ep(); if (!e || S.prompter == null) return;
    const beats = e.beats || []; const i = Math.max(0, Math.min(S.prompter, beats.length - 1)); S.prompter = i; const b = beats[i];
    $prompter.innerHTML = `<div class="prompter-bar"><button class="btn sm" data-p="close">Close</button><span class="meta">${i + 1} / ${beats.length}</span><span style="flex:1"></span>
        <button class="btn sm" data-p="smaller" aria-label="Smaller text">A−</button><button class="btn sm" data-p="bigger" aria-label="Bigger text">A+</button></div>
      <div class="prompter-body" id="pb"><div class="prompter-in" style="--scale:${S.scale}">
        <div class="k">${esc(b.kicker || "Beat " + (i + 1))} · ${esc(b.title)}</div>
        ${b.hook ? `<div class="hk">${esc(b.hook)}</div>` : ""}
        <div>${rich(b.body)}</div>
        ${b.handoff ? `<div class="jt">→ JT: ${inline(esc(b.handoff))}</div>` : ""}
      </div></div>
      <div class="prompter-nav"><button class="btn" data-p="prev" ${i === 0 ? "disabled" : ""}>← Previous</button><button class="btn primary" data-p="next" ${i === beats.length - 1 ? "disabled" : ""}>Next →</button></div>`;
    const pb = document.getElementById("pb"); if (pb) pb.scrollTop = 0;
  }
  $prompter.addEventListener("click", ev => {
    const a = ev.target.closest("[data-p]")?.dataset.p; if (!a) return;
    if (a === "close") closePrompter();
    if (a === "next") { S.prompter++; renderPrompter(); }
    if (a === "prev") { S.prompter--; renderPrompter(); }
    if (a === "bigger") { S.scale = Math.min(2, S.scale + 0.1); saveScale(); renderPrompter(); }
    if (a === "smaller") { S.scale = Math.max(0.6, S.scale - 0.1); saveScale(); renderPrompter(); }
  });
  document.addEventListener("keydown", ev => {
    if (S.prompter == null) return;
    if (ev.key === "Escape") closePrompter();
    if (ev.key === "ArrowRight" || ev.key === "PageDown") { const n = (ep()?.beats || []).length; if (S.prompter < n - 1) { S.prompter++; renderPrompter(); } }
    if (ev.key === "ArrowLeft" || ev.key === "PageUp") { if (S.prompter > 0) { S.prompter--; renderPrompter(); } }
  });
  function saveScale() { try { localStorage.setItem("pm-scale", String(S.scale)); } catch (_) {} }
  try { const v = parseFloat(localStorage.getItem("pm-scale")); if (v) S.scale = v; } catch (_) {}

  // ---------- actions ----------
  function stopEditing() { S.editing = null; S.confirmDel = null; render(true); }
  $app.addEventListener("click", async ev => {
    try {
    const t = ev.target.closest("[data-act]"); if (!t) return;
    const a = t.dataset.act, e = ep();
    if (t.tagName === "BUTTON" && t.closest("summary")) ev.preventDefault();
    switch (a) {
      case "tab": S.tab = t.dataset.tab; S.editing = null; S.confirmDel = null; render(true); break;
      case "new-ep": S.newEp = true; render(true); break;
      case "cancel-new": S.newEp = false; render(true); break;
      case "edit-head": S.editing = "head"; S.confirmDel = null; render(true); break;
      case "edit": S.editing = t.dataset.key; S.confirmDel = null; render(true); break;
      case "cancel-edit": stopEditing(); break;
      case "ask-del": S.confirmDel = t.dataset.what; render(true); break;
      case "no-del": S.confirmDel = null; render(true); break;
      case "del-item": await deleteEditing(); break;
      case "del-episode": if (e) { const id = e.id; await write("episodes/" + id, r => r.delete(), "Episode deleted"); S.editing = null; S.confirmDel = null; location.hash = "episodes"; render(true); } break;
      case "move": moveItem(t.dataset.list, t.dataset.id, Number(t.dataset.dir)); break;
      case "toggle-check": break;
      case "del-check": if (e) patchEp({ checklist: (e.checklist || []).filter(c => c.id !== t.dataset.id) }); render(true); break;
      case "prompter": openPrompter(Number(t.dataset.idx)); break;
      case "toggle-idea": { const i = S.ideas.find(x => x.id === t.dataset.id); if (i) { await write("ideas/" + i.id, r => r.update({ used: !i.used })); render(true); } break; }
    }
    } catch (error) { toast(error.message); }
  });
  $app.addEventListener("change", ev => {
    const t = ev.target; if (t.dataset.act !== "toggle-check") return;
    const e = ep(); if (!e) return;
    const list = (e.checklist || []).map(c => c.id === t.dataset.id ? { ...c, done: t.checked } : c);
    patchEp({ checklist: list }); render(true);
  });
  $app.addEventListener("toggle", ev => {
    const d = ev.target; if (!(d instanceof HTMLDetailsElement) || !d.dataset.sec) return;
    const e = ep(); if (!e || S.canWrite === false) return;
    const collapsed = !d.open; const s = (e.sections || []).find(x => x.id === d.dataset.sec);
    if (!s || !!s.collapsed === collapsed) return;
    patchEp({ sections: e.sections.map(x => x.id === s.id ? { ...x, collapsed } : x) });
  }, true);

  function moveItem(listName, id, dir) {
    const e = ep(); if (!e) return;
    const arr = [...(e[listName] || [])]; const i = arr.findIndex(x => x.id === id); const j = i + dir;
    if (i < 0 || j < 0 || j >= arr.length) return;
    [arr[i], arr[j]] = [arr[j], arr[i]];
    patchEp({ [listName]: arr }); render(true);
  }
  async function deleteEditing() {
    const k = S.editing || ""; const e = ep();
    if (k.startsWith("idea:")) { const id = k.slice(5); await write("ideas/" + id, r => r.delete(), "Idea deleted"); }
    else if (e) {
      const [kind, id] = k.split(":");
      const list = { sec: "sections", beat: "beats", clip: "clips" }[kind];
      if (list) await patchEp({ [list]: (e[list] || []).filter(x => x.id !== id) }, "Deleted");
    }
    stopEditing();
  }

  const val = id => (document.getElementById(id)?.value ?? "").trim();
  const valRaw = id => (document.getElementById(id)?.value ?? "").replace(/\s+$/, "");
  function upsert(listName, id, fields) {
    const e = ep(); if (!e) return;
    const arr = [...(e[listName] || [])];
    if (id === "new") arr.push({ id: uid(), ...fields });
    else { const i = arr.findIndex(x => x.id === id); if (i >= 0) arr[i] = { ...arr[i], ...fields }; }
    return patchEp({ [listName]: arr }, "Saved");
  }
  $app.addEventListener("submit", async ev => {
    try {
    ev.preventDefault();
    const f = ev.target, kind = f.dataset.form, id = f.dataset.id, e = ep();
    if (kind === "decision" && e) {
      const action = ev.submitter?.value;
      const note = val("decision-note"), cover = f.elements.cover.value;
      const errorBox = document.getElementById("decision-error");
      if (action === "request-changes" && !note) { errorBox.textContent = "Please describe the changes you want."; return; }
      const option = e.review.covers.find(c => c.id === cover);
      if (action === "approve" && !confirm(`Publish ${e.review.title} with cover ${option.label}?`)) return;
      const buttons = [...f.querySelectorAll("button")]; buttons.forEach(b => b.disabled = true);
      errorBox.textContent = "Sending decision to the publishing thread...";
      try {
        const doc = await api(`episodes/${e.id}/${action}`, "POST", {cover, note, ifVersion: e.version});
        replaceDoc("episodes", doc); S.error = null; render(true);
      } catch (error) {
        // Re-render a failed delivery so its recorded decision and new version are visible.
        if (ep()?.version !== e.version) render(true);
        const box = document.getElementById("decision-error"); if (box) box.textContent = error.message;
        buttons.forEach(b => b.disabled = false);
      }
      return;
    }
    if (kind === "new-ep") {
      const date = val("ne-date"), title = val("ne-title"); if (!date || !title) return;
      let docId = date, n = 2; while (S.episodes.some(x => x.id === docId)) docId = date + "-" + n++;
      const body = { date, title, status: "planning", time: "7:00 PM ET", summary: "", sections: [], beats: [], clips: [], checklist: [
        { id: uid(), text: "Say the on-air open: \"I'm JT. This is Matt. This is Peak Mind.\"", done: false },
        { id: uid(), text: "Before Q&A, say clearly: \"That's the end of the podcast.\"", done: false }], createdAt: Date.now() };
      await write("episodes/" + docId, r => r.set(body), "Episode added"); S.newEp = false;
      location.hash = "ep-" + docId; render(true); return;
    }
    if (kind === "head" && e) {
      await patchEp({ title: val("h-title"), time: val("h-time"), status: val("h-status"), summary: val("h-summary"), spaceUrl: val("h-space"), promoUrl: val("h-promo"), spotifyUrl: val("h-spotify") }, "Saved");
      return stopEditing();
    }
    if (kind === "section") { await upsert("sections", id, { heading: val("f-heading"), body: valRaw("f-body") }); return stopEditing(); }
    if (kind === "beat") { await upsert("beats", id, { kicker: val("b-kicker"), title: val("b-title"), hook: val("b-hook"), body: valRaw("b-body"), handoff: val("b-handoff") }); return stopEditing(); }
    if (kind === "clip") { await upsert("clips", id, { title: val("c-title"), status: val("c-status"), hook: val("c-hook"), ends: val("c-ends"), start: val("c-start"), end: val("c-end"), note: valRaw("c-note"), link: val("c-link") }); return stopEditing(); }
    if (kind === "note") { await patchEp({ scriptNote: valRaw("f-note") }, "Saved"); return stopEditing(); }
    if (kind === "add-check" && e) {
      const text = val("new-check"); if (!text) return;
      await patchEp({ checklist: [...(e.checklist || []), { id: uid(), text, done: false }] }); render("clear");
      document.getElementById("new-check")?.focus(); return;
    }
    if (kind === "add-idea") {
      const text = val("new-idea"); if (!text) return;
      const nid = uid(); const body = { text, used: false, createdAt: Date.now() };
      await write("ideas/" + nid, r => r.set(body), "Idea added"); render("clear");
      document.getElementById("new-idea")?.focus(); return;
    }
    if (kind === "idea") {
      const i = S.ideas.find(x => x.id === id); const text = valRaw("i-text");
      if (i && text) { await write("ideas/" + id, r => r.update({ text }), "Saved"); }
      return stopEditing();
    }
    } catch (error) { toast(error.message); }
  });

  // Polling pauses in hidden tabs, active forms, the prompter, and playing audio.
  // A form keeps its original version so a concurrent agent write returns a conflict.
  let etag = null, polling = false;
  function busy() {
    return S.editing || S.newEp || S.prompter != null || $app.querySelector("input[type=radio][data-dirty]") ||
      [...$app.querySelectorAll("input:not([type=checkbox]):not([type=radio]), textarea")].some(x => x.value && (x.matches(":focus") || x.dataset.dirty)) ||
      [...$app.querySelectorAll("audio")].some(x => !x.paused);
  }
  $app.addEventListener("input", ev => { ev.target.dataset.dirty = "1"; });
  async function poll() {
    if (document.hidden || polling || (S.loaded && busy())) return;
    polling = true;
    try {
      const response = await fetch("/api/state", {headers: etag ? {"If-None-Match": etag} : {}});
      if (response.status === 304) { if (S.slow) { S.slow = false; render(); } return; }
      if (!response.ok) throw new Error("Cannot load local Studio data");
      const data = await response.json();
      if (S.loaded && busy()) return;
      etag = response.headers.get("ETag");
      const wasLoaded = S.loaded, previous = ep();
      S.episodes = data.episodes; S.ideas = data.ideas; S.loaded = true; S.slow = false;
      if (S.openId && !ep()) { S.openId = null; S.editing = null; }
      if ((!wasLoaded || previous?.status !== "review") && ep()?.status === "review") S.tab = "review";
      render();
    } catch (error) { S.slow = true; if (!S.loaded) S.error = error.message; render(); }
    finally { polling = false; }
  }
  readHash(); render(true);
  api("me").then(me => { S.me = me; S.canWrite = me.canEdit; return poll(); }).catch(error => { S.error = error.message; render(true); });
  setInterval(poll, 4000);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) poll(); });
  try { document.documentElement.dataset.theme = localStorage.getItem("pm-theme") || ""; } catch (_) {}
  document.getElementById("theme-toggle").addEventListener("click", () => {
    const dark = document.documentElement.dataset.theme === "dark" || (!document.documentElement.dataset.theme && matchMedia("(prefers-color-scheme: dark)").matches);
    document.documentElement.dataset.theme = dark ? "light" : "dark";
    try { localStorage.setItem("pm-theme", dark ? "light" : "dark"); } catch (_) {}
  });
})();
