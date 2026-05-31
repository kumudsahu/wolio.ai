/* "My Learning Universe" home + Worlds + Life Learning Timeline. */
window.Home = (function () {
  let me = null, worlds = [], tl = null, tab = "home";

  async function enter(opts = {}) {
    await refresh();
    Mentor.mount();
    if (opts.playFirst) {
      const j = opts.playFirst;
      renderHome();
      setTimeout(() => playMission(j.first_mission.world, j.first_mission.id, j.first_mission.title, j.first_mission.emoji), 350);
    } else {
      renderHome();
    }
  }

  async function refresh() {
    const id = App.userId();
    [me, , tl] = await Promise.all([API.me(id), null, API.timeline(id)]);
    const w = await API.worlds(id);
    worlds = w.worlds;
  }

  const greet = () => {
    const h = new Date().getHours();
    if (h < 12) return "Good morning";
    if (h < 17) return "Hey";
    return "Good evening";
  };

  /* ---------------- HOME ---------------- */
  function renderHome() {
    tab = "home";
    const D = window.DATA;
    const primary = worlds[0];
    const last = tl.years[0] && tl.years[0].concepts[0];
    const html = `
      <div class="home-head fadein">
        <div class="mascot sm">${me.avatar.emoji || "🦊"}</div>
        <div class="who">
          <h2>${greet()}, ${UI.esc(me.name)} 👋</h2>
          <p>Ready to continue your ${primary ? UI.esc(primary.name) : "adventure"}?</p>
        </div>
        <div class="xpchip">⭐ ${me.xp}</div>
      </div>

      <!-- 2. Continue journey -->
      <div class="section fadein delay-1">
        <div class="resume" style="background:linear-gradient(135deg, ${primary ? primary.color : "#7c5cff"}, #ff6ba6)">
          <div class="tag">▶ Continue your journey</div>
          <h3>${primary ? primary.emoji + " " + UI.esc(primary.missions[0].title) : "Start your first mission"}</h3>
          <p>${primary ? "Pick up right where you left off." : "Your universe is waiting."}</p>
          <span class="play" id="resume">▶ Resume</span>
        </div>
      </div>

      <!-- 3. Learning worlds -->
      <div class="section fadein delay-2">
        <div class="section-h"><h3>🌌 Learning Worlds</h3><a id="seeworlds">See all</a></div>
        <div class="rail">
          ${worlds.map((w) => worldCard(w)).join("")}
        </div>
      </div>

      <!-- 4. Quick learn -->
      <div class="section fadein delay-2">
        <div class="section-h"><h3>⚡ Quick Learn</h3><span class="muted" style="font-size:12px">swipe →</span></div>
        <div class="rail">
          ${D.quickLearn.map((q) => `
            <div class="reel">
              <div class="q">${q.q}</div>
              <div class="go">${q.go} →</div>
            </div>`).join("")}
        </div>
      </div>

      <!-- 5. Daily quests -->
      <div class="section fadein delay-3">
        <div class="section-h"><h3>🔥 Daily Quests</h3><span class="pill">🔥 ${me.streak} day streak</span></div>
        <div class="stack">
          ${D.quests.map((q) => `
            <div class="quest"><div class="qi">${q.icon}</div>
              <div class="qt"><b>${q.t}</b><span>Tap a world to begin</span></div>
              <div class="qx">${q.x}</div></div>`).join("")}
        </div>
      </div>

      <!-- 6. Progress snapshot -->
      <div class="section fadein delay-3">
        <div class="section-h"><h3>📊 Today's Progress</h3></div>
        <div class="tiles">
          <div class="tile"><b>${tl.total_concepts}</b><span>concepts</span></div>
          <div class="tile"><b>${tl.memory_strength}%</b><span>memory 🧠</span></div>
          <div class="tile"><b>${me.streak}</b><span>day streak</span></div>
        </div>
      </div>

      <!-- 7. Your memory -->
      <div class="section fadein delay-4">
        <div class="section-h"><h3>🧬 Your Memory</h3><a id="seemem">Open timeline</a></div>
        <div class="memcard">
          <div class="mtitle">${last ? "You learned " + UI.esc(last.title) + " " + ago(last.learned_at) : "Your brain archive starts here"}</div>
          <div class="mstrength"><i style="width:${tl.memory_strength}%"></i></div>
          <div class="muted" style="font-size:13px">${tl.needs_revision.length ? tl.needs_revision.length + " concepts want a quick revision" : "Everything's fresh! Keep going 🔥"}</div>
        </div>
      </div>

      ${tabbar("home")}
    `;
    UI.render(html);
    document.getElementById("resume").onclick = () => primary
      ? playMission(primary.id, primary.missions[0].id, primary.missions[0].title, primary.missions[0].emoji)
      : UI.toast("Pick a world to begin!");
    document.getElementById("seeworlds").onclick = renderWorlds;
    document.getElementById("seemem").onclick = renderMemory;
    document.querySelectorAll("[data-world]").forEach((el) => {
      el.onclick = () => openWorld(el.dataset.world);
    });
    wireTabs();
  }

  function worldCard(w) {
    const done = countLearned(w);
    const pct = Math.min(100, Math.round((done / Math.max(1, w.missions.length)) * 100));
    return `
      <div class="world" data-world="${w.id}" style="background:linear-gradient(160deg, ${w.color}, rgba(11,7,32,.65))">
        <div class="wemoji">${w.emoji}</div>
        <div>
          <h4>${UI.esc(w.name)}</h4>
          <small>${UI.esc(w.subject)} · ${done}/${w.missions.length}</small>
          <div class="bar"><i style="width:${pct}%"></i></div>
        </div>
      </div>`;
  }

  function countLearned(w) {
    if (!tl) return 0;
    const titles = new Set();
    tl.years.forEach((y) => y.concepts.forEach((c) => { if (c.world === w.name) titles.add(c.title); }));
    return titles.size;
  }

  /* ---------------- WORLDS ---------------- */
  function renderWorlds() {
    tab = "worlds";
    UI.render(`
      <div class="home-head fadein"><div class="who"><h2>🌌 Learning Worlds</h2><p>Choose your next adventure</p></div></div>
      <div class="stack fadein delay-1" style="margin-top:8px">
        ${worlds.map((w) => `
          <div class="world" data-world="${w.id}" style="flex:1;height:auto;flex-direction:row;align-items:center;gap:14px;background:linear-gradient(120deg, ${w.color}, rgba(11,7,32,.6))">
            <div class="wemoji">${w.emoji}</div>
            <div style="flex:1">
              <h4>${UI.esc(w.name)}</h4>
              <small>${UI.esc(w.tagline)}</small>
              <div class="bar"><i style="width:${Math.round((countLearned(w)/Math.max(1,w.missions.length))*100)}%"></i></div>
            </div>
            <div style="font-size:22px">→</div>
          </div>`).join("")}
      </div>
      ${tabbar("worlds")}
    `);
    document.querySelectorAll("[data-world]").forEach((el) => el.onclick = () => openWorld(el.dataset.world));
    wireTabs();
  }

  function openWorld(id) {
    const w = worlds.find((x) => x.id === id);
    if (!w) return;
    UI.render(`
      <div class="home-head fadein">
        <button class="pill" onclick="Home._back()">←</button>
        <div class="who"><h2>${w.emoji} ${UI.esc(w.name)}</h2><p>${UI.esc(w.tagline)}</p></div>
      </div>
      <div class="stack fadein delay-1" style="margin-top:10px">
        ${w.missions.map((m, i) => `
          <div class="quest" data-m="${m.id}" data-title="${UI.esc(m.title)}" data-e="${m.emoji}" style="cursor:pointer">
            <div class="qi">${m.emoji}</div>
            <div class="qt"><b>Mission ${i + 1}: ${UI.esc(m.title)}</b><span>Learn: ${UI.esc(m.concept)}</span></div>
            <div class="qx">▶</div>
          </div>`).join("")}
      </div>
      ${tabbar("worlds")}
    `);
    document.querySelectorAll("[data-m]").forEach((el) =>
      el.onclick = () => playMission(w.id, el.dataset.m, el.dataset.title, el.dataset.e));
    wireTabs();
  }

  /* ---------------- PLAY MISSION (mini interactive) ---------------- */
  async function playMission(worldId, missionId, title, emoji) {
    UI.render(`
      <div class="builder">
        <div class="mascot" style="font-size:64px">${emoji || "🚀"}</div>
        <h1 class="title center" style="margin:0">${UI.esc(title)}</h1>
        <p class="muted center" style="max-width:280px">Tap below to complete the mission and lock this concept into your brain forever 🧠</p>
        <button class="btn" id="finish">Complete mission ✨</button>
      </div>
    `);
    document.getElementById("finish").onclick = async () => {
      try {
        const r = await API.completeMission(App.userId(), worldId, missionId);
        await refresh();
        UI.toast(`+${r.xp_earned} XP · ${r.emoji} ${r.concept_saved} saved to your timeline!`);
        renderHome();
      } catch (e) {
        UI.toast("Couldn't save — try again");
      }
    };
  }

  /* ---------------- MEMORY / TIMELINE ---------------- */
  function renderMemory() {
    tab = "memory";
    const empty = tl.total_concepts === 0;
    UI.render(`
      <div class="home-head fadein"><div class="who"><h2>🧬 Your Memory</h2><p>Everything you've ever learned</p></div>
        <div class="xpchip" style="background:rgba(52,224,161,.16);color:var(--green);border-color:rgba(52,224,161,.3)">🧠 ${tl.memory_strength}%</div></div>

      <div class="searchbar fadein delay-1">
        <input id="brainq" placeholder="🔍 Search your brain… (planets, fractions)" />
      </div>

      <div class="tiles fadein delay-1" style="margin-bottom:6px">
        <div class="tile"><b>${tl.total_concepts}</b><span>learned</span></div>
        <div class="tile"><b>${tl.mastered}</b><span>mastered</span></div>
        <div class="tile"><b>${tl.memory_strength}%</b><span>strength</span></div>
      </div>

      <button class="btn btn--block fadein delay-2" id="revise" style="margin:10px 0">⚡ Revise everything I've learned</button>

      <div id="tlbody" class="fadein delay-2">
        ${empty ? emptyState() : tl.years.map(yearBlock).join("")}
      </div>
      ${tabbar("memory")}
    `);
    const q = document.getElementById("brainq");
    q.addEventListener("input", debounce(async () => {
      const term = q.value.trim();
      const body = document.getElementById("tlbody");
      if (!term) { body.innerHTML = tl.years.map(yearBlock).join("") || emptyState(); return; }
      const r = await API.searchBrain(App.userId(), term);
      body.innerHTML = r.results.length
        ? `<div class="muted" style="margin:6px 0 10px">${r.results.length} memories for "${UI.esc(term)}"</div>` + r.results.map(conceptCard).join("")
        : `<div class="empty"><span class="em">🔍</span>No memory of "${UI.esc(term)}" yet.<br>Go learn it!</div>`;
    }, 220));
    document.getElementById("revise").onclick = openReviseSheet;
    wireTabs();
  }

  function yearBlock(y) {
    return `<div class="year">
      <div class="yh"><b>${y.year}</b><span>${y.count} concept${y.count > 1 ? "s" : ""}</span></div>
      ${y.concepts.map(conceptCard).join("")}
    </div>`;
  }
  function conceptCard(c) {
    return `<div class="cmcard">
      <div class="ce">${c.emoji || "✨"}</div>
      <div class="ci"><b>${UI.esc(c.title)}</b><span>${UI.esc(c.learned_via || c.subject)} · ${ago(c.learned_at)}</span></div>
      <div class="cm">${c.memory_strength}%</div>
    </div>`;
  }
  function emptyState() {
    return `<div class="empty"><span class="em">🧠</span><b>Your brain archive is empty… for now.</b><br>
      Complete a mission and watch it appear here forever.</div>`;
  }

  /* ---------------- REVISION ---------------- */
  function openReviseSheet() {
    const scopes = [
      { id: "last_7", label: "Last 7 days", emoji: "📅" },
      { id: "last_year", label: "Last 1 year", emoji: "🗓️" },
      { id: "all", label: "Entire journey", emoji: "🌍" },
      { id: "needs_revision", label: "What I'm forgetting", emoji: "🧠" },
    ];
    const sheet = UI.h(`
      <div class="sheet"><div class="scrim"></div>
        <div class="panel">
          <div class="phead"><b>⚡ Revise</b><small>&nbsp;pick a scope</small><button class="close">✕</button></div>
          <div class="stack" style="padding:16px">
            ${scopes.map((s) => `<button class="quest" data-s="${s.id}" style="text-align:left"><div class="qi">${s.emoji}</div><div class="qt"><b>${s.label}</b></div><div class="qx">▶</div></button>`).join("")}
          </div>
        </div></div>`);
    document.querySelector(".stage").appendChild(sheet);
    const close = () => sheet.remove();
    sheet.querySelector(".scrim").onclick = close;
    sheet.querySelector(".close").onclick = close;
    sheet.querySelectorAll("[data-s]").forEach((b) => b.onclick = async () => {
      close();
      const r = await API.revise(App.userId(), b.dataset.s);
      if (!r.count) { UI.toast("Nothing to revise here yet!"); return; }
      runFlashcards(r.cards, 0);
    });
  }

  function runFlashcards(cards, i) {
    if (i >= cards.length) {
      refresh().then(() => { UI.toast("🔥 Revision done! Memory refreshed."); renderMemory(); });
      return;
    }
    const c = cards[i];
    UI.render(`
      <div class="home-head"><div class="who"><h2>⚡ Revision</h2><p>Card ${i + 1} of ${cards.length}</p></div>
        <div class="xpchip">${i + 1}/${cards.length}</div></div>
      <div class="flash" id="flash">
        <div class="inner">
          <div class="face"><div style="font-size:54px">${c.emoji}</div><h2 style="margin:0">${UI.esc(c.front)}</h2><p class="muted">tap to flip</p></div>
          <div class="face back"><h2 style="margin:0">${UI.esc(c.title)}</h2><p>${UI.esc(c.summary || c.subject)}</p><p class="muted">Learned via ${UI.esc(c.learned_via || "Wolio")}</p></div>
        </div>
      </div>
      <div class="cta-bar stack">
        <button class="btn btn--block" id="next">${i + 1 < cards.length ? "Got it → next" : "Finish 🎉"}</button>
      </div>
    `);
    const flash = document.getElementById("flash");
    flash.onclick = () => flash.classList.toggle("flipped");
    document.getElementById("next").onclick = () => runFlashcards(cards, i + 1);
  }

  /* ---------------- PARENT GATE ---------------- */
  function parentGate() {
    tab = "parent";
    let pin = "";
    UI.render(`
      <div class="home-head fadein"><div class="who"><h2>👨‍👩‍👧 Parent Zone</h2><p>Enter PIN to view reports</p></div></div>
      <div class="center fadein delay-1" style="margin-top:30px">
        <div class="mascot" style="background:var(--grad-cta)">🔒</div>
        <div id="pindots" class="progress-dots" style="margin-top:16px"></div>
      </div>
      <div class="choices grid-3 fadein delay-2" id="pad" style="margin-top:20px">
        ${[1,2,3,4,5,6,7,8,9].map((n) => `<button class="choice" data-n="${n}" style="font-size:24px">${n}</button>`).join("")}
        <button class="choice" data-n="del" style="font-size:20px">⌫</button>
        <button class="choice" data-n="0" style="font-size:24px">0</button>
        <button class="choice" data-n="ok" style="font-size:20px">✓</button>
      </div>
      <p class="muted center" style="margin-top:14px">Demo PIN: <b>1234</b></p>
      ${tabbar("parent")}
    `);
    const draw = () => document.getElementById("pindots").innerHTML =
      [0,1,2,3].map((i) => `<i class="${i < pin.length ? "active" : ""}"></i>`).join("");
    draw();
    document.querySelectorAll("#pad .choice").forEach((b) => b.onclick = () => {
      const n = b.dataset.n;
      if (n === "del") pin = pin.slice(0, -1);
      else if (n === "ok") { pin === "1234" ? parentDashboard() : (UI.toast("Wrong PIN"), pin = ""); }
      else if (pin.length < 4) pin += n;
      draw();
      if (pin.length === 4 && pin === "1234") parentDashboard();
    });
    wireTabs();
  }

  function parentDashboard() {
    const interests = me.interests.join(", ") || "exploring";
    UI.render(`
      <div class="home-head fadein"><button class="pill" onclick="Home._tab('parent')">←</button>
        <div class="who"><h2>${UI.esc(me.name)}'s Growth Story</h2><p>AI Learning DNA</p></div></div>
      <div class="memcard fadein delay-1" style="margin-top:8px">
        <div class="mtitle">🧠 ${me.name} has learned <b>${tl.total_concepts}</b> concepts</div>
        <div class="mstrength"><i style="width:${tl.memory_strength}%"></i></div>
        <div class="muted" style="font-size:13px">Memory strength ${tl.memory_strength}% · ${tl.mastered} mastered</div>
      </div>
      <div class="tiles fadein delay-2" style="margin-top:14px">
        <div class="tile"><b>${me.xp}</b><span>total XP</span></div>
        <div class="tile"><b>${me.streak}</b><span>day streak</span></div>
        <div class="tile"><b>${tl.mastered}</b><span>mastered</span></div>
      </div>
      <div class="section fadein delay-2"><div class="section-h"><h3>Interest map</h3></div>
        <div class="quest"><div class="qi">❤️</div><div class="qt"><b>Loves</b><span>${UI.esc(interests)}</span></div></div>
      </div>
      <div class="section fadein delay-3"><div class="section-h"><h3>AI insight</h3></div>
        <div class="bubble">${UI.esc(me.name)} is building strong curiosity in ${UI.esc(me.interests[0] || "science")}. Keep the daily streak alive for compounding growth 🔥</div>
      </div>
      <button class="btn btn--block fadein delay-3" style="margin-top:16px" onclick="UI.toast('Premium: AI Learning DNA report 📄')">📄 Generate AI Learning DNA report</button>
      ${tabbar("parent")}
    `);
    wireTabs();
  }

  /* ---------------- nav ---------------- */
  function tabbar(active) {
    const items = [
      { id: "home", i: "🏠", t: "Home" },
      { id: "worlds", i: "🌌", t: "Worlds" },
      { id: "memory", i: "🧬", t: "Memory" },
      { id: "parent", i: "👨‍👩‍👧", t: "Parent" },
    ];
    return `<nav class="tabbar">${items.map((x) =>
      `<button data-tab="${x.id}" class="${x.id === active ? "active" : ""}"><span class="ti">${x.i}</span>${x.t}</button>`).join("")}</nav>`;
  }
  function wireTabs() {
    document.querySelectorAll("[data-tab]").forEach((b) => b.onclick = () => _tab(b.dataset.tab));
  }
  function _tab(t) {
    if (t === "home") renderHome();
    else if (t === "worlds") renderWorlds();
    else if (t === "memory") renderMemory();
    else if (t === "parent") parentGate();
  }
  function _back() { _tab(tab); }

  /* utils */
  function ago(ts) {
    if (!ts) return "just now";
    const d = (Date.now() - new Date(ts.replace(" ", "T") + "Z").getTime()) / 86400000;
    if (d < 1) return "today";
    if (d < 2) return "yesterday";
    if (d < 30) return Math.floor(d) + " days ago";
    return Math.floor(d / 30) + " months ago";
  }
  function debounce(fn, ms) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }

  return { enter, renderHome, _tab, _back, getMe: () => me };
})();
