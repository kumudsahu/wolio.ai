/* Parent Dashboard + Premium system (Step 6).
   Rendered behind the PIN gate (Home.parentGate → parentDashboard → Parent.open). */
window.Parent = (function () {
  let D = null;            // current dashboard payload
  let idleTimer = null;    // auto-logout after inactivity (security)
  const tab = () => Home.tabbar("profile");
  const wire = () => Home.wireTabs();
  const cid = () => App.userId();

  function armIdle() {
    clearTimeout(idleTimer);
    idleTimer = setTimeout(() => {
      if (document.querySelector(".screen[data-parent]")) {
        UI.toast("Parent mode locked (inactivity) 🔒");
        Home._tab("home");
      }
    }, 90000);
  }

  async function open(childId) {
    UI.render(`<div class="builder"><div class="ring"></div><p class="build-step">Building parent dashboard…</p></div>`);
    try { D = await API.parentDashboard(childId); }
    catch (e) { UI.toast("Couldn't load dashboard"); return Home._tab("profile"); }
    render();
  }

  function render() {
    const s = D.summary, premium = D.plan !== "free";
    const topInterest = D.interests[0];
    const maxInt = Math.max(1, ...D.interests.map((i) => i.pct));
    UI.render(`
      <div class="home-head fadein"><button class="pill" onclick="Home._tab('profile')">←</button>
        <div class="who"><h2>${UI.esc(D.child.name)}'s Dashboard</h2><p>${UI.esc(D.child.tier)} · age ${UI.esc(D.child.age_group)}</p></div>
        <button class="avatar-btn" id="switch"><span>${D.child.avatar}</span></button>
      </div>

      <!-- premium banner -->
      ${premium
        ? `<div class="premium-banner on fadein">👑 Premium active — full analytics & reports unlocked</div>`
        : `<div class="premium-banner fadein"><div><b>🔓 Unlock Premium</b><span>Full skill analytics, AI DNA report & more</span></div><button class="btn" id="upgrade" style="padding:10px 16px">Upgrade</button></div>`}

      <!-- A: learning summary -->
      <div class="section fadein delay-1"><div class="section-h"><h3>🧠 Learning summary</h3></div>
        <div class="tiles">
          <div class="tile"><b>${s.concepts}</b><span>concepts</span></div>
          <div class="tile"><b>${s.learning_time_today}m</b><span>today</span></div>
          <div class="tile"><b>🔥 ${s.streak}</b><span>streak</span></div>
        </div>
      </div>

      <!-- B: skill growth (the star) -->
      <div class="section fadein delay-1"><div class="section-h"><h3>📈 Skill growth</h3></div>
        <div class="skills">
          ${D.skills.map((sk) => `
            <div class="skill-row">
              <div class="sk-label">${sk.icon} ${UI.esc(sk.label)}</div>
              <div class="sk-bar"><i style="width:${sk.score}%;background:${skColor(sk.score)}"></i></div>
              <div class="sk-val">${sk.score}%</div>
            </div>`).join("")}
        </div>
        <div class="bubble" style="margin-top:12px">🤖 ${UI.esc(D.skill_insight)}</div>
      </div>

      <!-- C: interest mapping -->
      <div class="section fadein delay-2"><div class="section-h"><h3>🎯 Interest map</h3></div>
        ${D.interests.length ? `<div class="stack">
          ${D.interests.map((i) => `
            <div class="int-row"><span class="int-label">${Home.subjEmoji(i.label)} ${UI.esc(i.label)}</span>
              <div class="int-bar"><i style="width:${Math.round(i.pct / maxInt * 100)}%"></i></div>
              <span class="int-pct">${i.pct}%</span></div>`).join("")}
        </div>` : `<div class="muted">Interests emerge as your child explores.</div>`}
        <div class="muted" style="font-size:13px;margin-top:8px">${UI.esc(D.interest_insight)}</div>
      </div>

      <!-- D: weak areas -->
      <div class="section fadein delay-2"><div class="section-h"><h3>⚠️ Areas to support</h3></div>
        ${D.weak_areas.length ? D.weak_areas.map((w) => `
          <div class="quest"><div class="qi">📌</div>
            <div class="qt"><b>${UI.esc(w.subject)} · ${w.avg_mastery}%</b><span>${UI.esc(w.concepts.join(", ") || "needs practice")}</span></div>
            <button class="pill" onclick="Parent._reviseHint()">Revise</button></div>`).join("")
          : `<div class="quest"><div class="qi">✅</div><div class="qt"><b>No weak areas!</b><span>${UI.esc(D.child.name)} is on track everywhere.</span></div></div>`}
      </div>

      <!-- retention -->
      <div class="section fadein delay-3"><div class="section-h"><h3>🧬 Memory & retention</h3></div>
        <div class="memcard"><div class="mtitle">Retention: <span class="ret ${retCls(D.retention.strength)}">${D.retention.label}</span> · ${D.retention.strength}%</div>
          <div class="mstrength"><i style="width:${D.retention.strength}%"></i></div>
          <div class="muted" style="font-size:13px">${D.retention.due.length ? D.retention.due.length + " concept(s) due for revision" : "Everything fresh in memory 🔥"}</div>
        </div>
      </div>

      <!-- goals + controls -->
      <div class="section fadein delay-3"><div class="section-h"><h3>🎯 Goals & controls</h3></div>
        <button class="quest" id="goals" style="text-align:left"><div class="qi">⏱️</div>
          <div class="qt"><b>Daily goal: ${D.goals.daily_min} min ${D.goals.on_track ? "✅" : ""}</b><span>${D.goals.subject ? "Focus: " + UI.esc(D.goals.subject) : "Tap to set a focus"} · ${D.goals.today_min}m today</span></div><div class="qx">→</div></button>
        <button class="quest" id="controls" style="text-align:left;margin-top:10px"><div class="qi">🚫</div>
          <div class="qt"><b>Screen limit: ${D.controls.screen_limit_min} min</b><span>${D.controls.used_today}m used today</span></div><div class="qx">→</div></button>
      </div>

      <!-- reports + DNA -->
      <div class="section fadein delay-4"><div class="section-h"><h3>📄 Reports</h3></div>
        <div class="row" style="gap:8px">
          <button class="btn btn--ghost" style="flex:1" onclick="Parent.report('weekly')">Weekly</button>
          <button class="btn btn--ghost" style="flex:1" onclick="Parent.report('monthly')">Monthly</button>
          <button class="btn btn--ghost" style="flex:1" onclick="Parent.report('annual')">Annual</button>
        </div>
        <button class="btn btn--block" id="dna" style="margin-top:12px">🧬 AI Learning DNA report ${premium ? "" : "🔒"}</button>
      </div>

      <!-- parent notifications -->
      ${D.notifications.length ? `<div class="section fadein delay-4"><div class="section-h"><h3>🔔 Updates</h3></div>
        <div class="stack">${D.notifications.map((n) => `<div class="quest"><div class="qi">${n.icon}</div><div class="qt"><b>${UI.esc(n.text)}</b></div></div>`).join("")}</div>
      </div>` : ""}

      ${tab()}
    `);
    // auto-logout guard: mark this screen + reset idle timer on interaction
    const root = document.querySelector(".screen");
    if (root) { root.dataset.parent = "1"; root.addEventListener("pointerdown", armIdle); }
    armIdle();

    const up = document.getElementById("upgrade");
    if (up) up.onclick = openUpgrade;
    document.getElementById("switch").onclick = openChildren;
    document.getElementById("goals").onclick = openGoals;
    document.getElementById("controls").onclick = openControls;
    document.getElementById("dna").onclick = () => premium ? openDna() : openUpgrade();
    wire();
  }

  const skColor = (v) => v >= 70 ? "var(--green)" : v >= 40 ? "var(--gold)" : "var(--pink)";
  const retCls = (v) => v >= 70 ? "ok" : v >= 40 ? "mid" : "low";
  function _reviseHint() { UI.toast("Switch to your child's Memory tab to revise 🧠"); }

  /* ---------- 6.4 AI Learning DNA ---------- */
  async function openDna() {
    UI.render(`<div class="builder"><div class="ring"></div><p class="build-step">Generating Learning DNA…</p></div>`);
    let d;
    try { d = await API.parentDna(cid()); }
    catch (e) { UI.toast("Couldn't generate"); return render(); }
    const r = d.report;
    UI.render(`
      <div class="home-head fadein"><button class="pill" onclick="Parent.open(${cid()})">←</button>
        <div class="who"><h2>🧬 Learning DNA</h2><p>${UI.esc(r.name)} · ${UI.esc(r.learning_style || "")}</p></div></div>
      <div class="dna fadein delay-1">
        <div class="dna-row"><b>📚 Learns best via</b><p>${UI.esc(r.best_method)}</p></div>
        <div class="dna-row"><b>💪 Strengths</b><p>${(r.strengths || []).map(UI.esc).join(", ")}</p></div>
        <div class="dna-row"><b>🌱 Growth areas</b><p>${(r.weaknesses || []).map(UI.esc).join(", ")}</p></div>
        <div class="dna-row"><b>🎯 Attention pattern</b><p>${UI.esc(r.attention_pattern)}</p></div>
        <div class="dna-skills">
          ${(r.skills || []).map((sk) => `<div class="dna-skill"><b>${sk.score}%</b><span>${UI.esc(sk.label)}</span></div>`).join("")}
        </div>
        <div class="bubble" style="margin-top:12px">${UI.esc(r.narrative)}</div>
      </div>
      <div class="cta-bar"><button class="btn btn--block" id="dl">⬇️ Download report (.html)</button></div>
      ${tab()}
    `);
    document.getElementById("dl").onclick = () => downloadReport(r);
    wire();
  }

  function downloadReport(r) {
    const html = `<!doctype html><meta charset="utf-8"><title>${r.name} — Learning DNA</title>
      <body style="font-family:system-ui;max-width:640px;margin:40px auto;color:#1a1340;line-height:1.6">
      <h1 style="color:#7c5cff">🧬 ${r.name}'s Learning DNA</h1>
      <p><b>Learns best via:</b> ${r.best_method}</p>
      <p><b>Strengths:</b> ${(r.strengths || []).join(", ")}</p>
      <p><b>Growth areas:</b> ${(r.weaknesses || []).join(", ")}</p>
      <p><b>Attention pattern:</b> ${r.attention_pattern}</p>
      <h3>Skills</h3><ul>${(r.skills || []).map((s) => `<li>${s.label}: ${s.score}%</li>`).join("")}</ul>
      <p style="background:#f3f0ff;padding:16px;border-radius:12px">${r.narrative}</p>
      <p style="color:#888">Generated by wolio.ai · Premium Learning DNA report</p></body>`;
    const blob = new Blob([html], { type: "text/html" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${r.name}-learning-dna.html`;
    a.click();
    UI.toast("Report downloaded 📄");
  }

  /* ---------- 6.10 period report ---------- */
  async function report(period) {
    let r;
    try { r = await API.parentReport(cid(), period); }
    catch (e) { return UI.toast("Couldn't load report"); }
    const sheet = UI.h(`
      <div class="sheet"><div class="scrim"></div><div class="panel">
        <div class="phead"><b>📄 ${period[0].toUpperCase() + period.slice(1)} report</b><button class="close">✕</button></div>
        <div style="padding:16px;max-height:70vh;overflow:auto">
          <div class="bubble" style="margin-bottom:14px">${UI.esc(r.headline)}</div>
          <div class="tiles" style="margin-bottom:14px">
            <div class="tile"><b>${r.learned}</b><span>learned</span></div>
            <div class="tile"><b>${r.missions}</b><span>missions</span></div>
            <div class="tile"><b>${r.revisions}</b><span>revised</span></div>
          </div>
          <div class="section-h"><h3>Recommendations</h3></div>
          <div class="stack">${r.recommendations.map((x) => `<div class="quest"><div class="qi">💡</div><div class="qt"><b>${UI.esc(x)}</b></div></div>`).join("")}</div>
        </div>
      </div></div>`);
    mountSheet(sheet);
  }

  /* ---------- 6.6 goals ---------- */
  function openGoals() {
    const mins = [10, 20, 30, 45, 60];
    const subjects = ["Science", "Math", "Literature", "History"];
    const sheet = UI.h(`
      <div class="sheet"><div class="scrim"></div><div class="panel">
        <div class="phead"><b>🎯 Set a goal</b><button class="close">✕</button></div>
        <div style="padding:16px">
          <h3 style="margin:0 0 10px">Daily learning time</h3>
          <div class="choices grid-3" id="mins">${mins.map((m) => `<button class="choice ${D.goals.daily_min === m ? "selected" : ""}" data-m="${m}">${m}m</button>`).join("")}</div>
          <h3 style="margin:16px 0 10px">Subject focus</h3>
          <div class="choices grid-2" id="subs">${subjects.map((su) => `<button class="choice ${D.goals.subject === su ? "selected" : ""}" data-s="${su}">${Home.subjEmoji(su)} ${su}</button>`).join("")}</div>
          <button class="btn btn--block" id="saveGoals" style="margin-top:16px">Save goal</button>
        </div>
      </div></div>`);
    let dm = D.goals.daily_min, sub = D.goals.subject;
    mountSheet(sheet);
    sheet.querySelectorAll("#mins .choice").forEach((b) => b.onclick = () => {
      sheet.querySelectorAll("#mins .choice").forEach((x) => x.classList.remove("selected"));
      b.classList.add("selected"); dm = +b.dataset.m;
    });
    sheet.querySelectorAll("#subs .choice").forEach((b) => b.onclick = () => {
      sheet.querySelectorAll("#subs .choice").forEach((x) => x.classList.remove("selected"));
      b.classList.add("selected"); sub = b.dataset.s;
    });
    sheet.querySelector("#saveGoals").onclick = async () => {
      await API.parentGoals({ child_id: cid(), daily_min: dm, subject: sub });
      sheet.remove(); UI.toast("Goal saved ✓"); open(cid());
    };
  }

  /* ---------- 6.7 screen controls ---------- */
  function openControls() {
    const lims = [30, 45, 60, 90, 120];
    const sheet = UI.h(`
      <div class="sheet"><div class="scrim"></div><div class="panel">
        <div class="phead"><b>🚫 Screen controls</b><button class="close">✕</button></div>
        <div style="padding:16px">
          <h3 style="margin:0 0 10px">Daily screen limit</h3>
          <div class="choices grid-3" id="lims">${lims.map((m) => `<button class="choice ${D.controls.screen_limit_min === m ? "selected" : ""}" data-m="${m}">${m}m</button>`).join("")}</div>
          <p class="muted" style="font-size:13px;margin-top:12px">Used today: ${D.controls.used_today} min. Wolio gently wraps up sessions at the limit.</p>
          <button class="btn btn--block" id="saveCtl" style="margin-top:10px">Save</button>
        </div>
      </div></div>`);
    let lim = D.controls.screen_limit_min;
    mountSheet(sheet);
    sheet.querySelectorAll("#lims .choice").forEach((b) => b.onclick = () => {
      sheet.querySelectorAll("#lims .choice").forEach((x) => x.classList.remove("selected"));
      b.classList.add("selected"); lim = +b.dataset.m;
    });
    sheet.querySelector("#saveCtl").onclick = async () => {
      await API.parentControls({ child_id: cid(), screen_limit_min: lim });
      sheet.remove(); UI.toast("Saved ✓"); open(cid());
    };
  }

  /* ---------- 6.9 premium upgrade ---------- */
  function openUpgrade() {
    const sheet = UI.h(`
      <div class="sheet"><div class="scrim"></div><div class="panel">
        <div class="phead"><b>👑 Go Premium</b><button class="close">✕</button></div>
        <div style="padding:16px">
          <div class="plan"><b>Free</b><span>Basic learning · limited insights</span><div class="plan-price">₹0</div></div>
          <div class="plan best"><div class="plan-tag">Best value</div><b>Premium</b><span>Full analytics · AI DNA report · personalized learning · advanced memory</span><div class="plan-price">₹8,000<small>/yr</small></div>
            <button class="btn btn--block" id="goPrem" style="margin-top:10px">Upgrade to Premium</button></div>
          <div class="plan"><b>Premium+ <span class="pill" style="font-size:10px">Soon</span></b><span>Tablet bundle · personal mentor</span><div class="plan-price">₹25k+</div></div>
        </div>
      </div></div>`);
    mountSheet(sheet);
    sheet.querySelector("#goPrem").onclick = async () => {
      await API.parentUpgrade(cid(), "premium");
      sheet.remove(); UI.confetti(); UI.toast("Welcome to Premium! 👑"); open(cid());
    };
  }

  /* ---------- 6.2 multi-child ---------- */
  async function openChildren() {
    let r;
    try { r = await API.parentChildren(cid()); }
    catch (e) { return UI.toast("Couldn't load children"); }
    const sheet = UI.h(`
      <div class="sheet"><div class="scrim"></div><div class="panel">
        <div class="phead"><b>👶 Children</b><button class="close">✕</button></div>
        <div class="stack" style="padding:16px;max-height:70vh;overflow:auto">
          ${r.children.map((c) => `
            <button class="quest" data-switch="${c.id}" style="text-align:left">
              <div class="qi">${c.avatar}</div>
              <div class="qt"><b>${UI.esc(c.name)} ${c.id === cid() ? "• active" : ""}</b><span>${UI.esc(c.tier)} · ${c.concepts} concepts · age ${UI.esc(c.age_group)}</span></div>
              <div class="qx">${c.id === cid() ? "✓" : "→"}</div></button>`).join("")}
          <button class="btn btn--block" id="addChild" style="margin-top:6px">➕ Add a child</button>
        </div>
      </div></div>`);
    mountSheet(sheet);
    sheet.querySelectorAll("[data-switch]").forEach((b) => b.onclick = () => {
      const id = +b.dataset.switch;
      sheet.remove();
      if (id !== cid()) { App.setUser(id); UI.toast("Switched child 🔄"); Home.enter({}); }
    });
    sheet.querySelector("#addChild").onclick = () => { sheet.remove(); openAddChild(); };
  }

  function openAddChild() {
    const ages = ["3-5", "6-8", "9-12", "13-16"];
    const ints = ["space", "animals", "cars", "stories", "games", "art", "sports", "music"];
    const sheet = UI.h(`
      <div class="sheet"><div class="scrim"></div><div class="panel">
        <div class="phead"><b>➕ Add a child</b><button class="close">✕</button></div>
        <div style="padding:16px">
          <input class="field" id="cname" placeholder="Child's name" maxlength="20" style="text-align:left;font-size:16px" />
          <h3 style="margin:14px 0 8px">Age</h3>
          <div class="choices grid-2" id="cage">${ages.map((a, i) => `<button class="choice ${i === 2 ? "selected" : ""}" data-a="${a}">${a}</button>`).join("")}</div>
          <h3 style="margin:14px 0 8px">Loves (pick a few)</h3>
          <div class="choices grid-3" id="cint">${ints.map((x) => `<button class="choice" data-i="${x}" style="font-size:12px">${x}</button>`).join("")}</div>
          <button class="btn btn--block" id="createChild" style="margin-top:16px">Create profile</button>
        </div>
      </div></div>`);
    let age = "9-12"; const picks = new Set();
    mountSheet(sheet);
    sheet.querySelectorAll("#cage .choice").forEach((b) => b.onclick = () => {
      sheet.querySelectorAll("#cage .choice").forEach((x) => x.classList.remove("selected"));
      b.classList.add("selected"); age = b.dataset.a;
    });
    sheet.querySelectorAll("#cint .choice").forEach((b) => b.onclick = () => {
      b.classList.toggle("selected");
      picks.has(b.dataset.i) ? picks.delete(b.dataset.i) : picks.add(b.dataset.i);
    });
    sheet.querySelector("#createChild").onclick = async () => {
      const name = sheet.querySelector("#cname").value.trim();
      if (name.length < 2) return UI.toast("Enter a name first");
      const res = await API.parentAddChild({ from_child_id: cid(), name, age_group: age, interests: [...picks] });
      sheet.remove(); UI.toast(`${name} added! 🎉`); openChildren();
    };
  }

  function mountSheet(sheet) {
    document.querySelector(".stage").appendChild(sheet);
    const close = () => sheet.remove();
    sheet.querySelector(".scrim").onclick = close;
    sheet.querySelector(".close").onclick = close;
  }

  return { open, report, openDna, _reviseHint };
})();
