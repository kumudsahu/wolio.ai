/* "My Learning Universe" homepage system (Step 2) + Worlds + Timeline + Profile.
   The home screen is driven by a single AI-built config from /api/homepage. */
window.Home = (function () {
  let me = null, worlds = [], tl = null, hp = null, tab = "home";
  let dismissed = new Set();           // notification ids the user has seen

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
    const [m, w, t, h] = await Promise.all([API.me(id), API.worlds(id), API.timeline(id), API.homepage(id)]);
    me = m; worlds = w.worlds; tl = t; hp = h;
  }

  const worldById = (id) => worlds.find((x) => x.id === id);
  const hpWorld = (id) => (hp.worlds || []).find((x) => x.id === id);

  /* ================= HOME ================= */
  function renderHome() {
    tab = "home";
    const g = hp.greeting, hero = hp.hero, cont = hp.continue;
    const unread = (hp.notifications || []).filter((n) => !dismissed.has(n.id)).length;

    UI.render(`
      <!-- 2.1 Top bar -->
      <div class="topbar fadein">
        <button class="avatar-btn" id="toProfile"><span>${me.avatar.emoji || "🦊"}</span></button>
        <div class="greet"><b>${g.text} ${g.emoji}</b><span>${hp.level.tier.emoji} ${hp.level.tier.name} · ${hp.stats.xp} XP</span></div>
        <span class="coinchip">🪙 ${hp.coins}</span>
        <button class="icon-btn" id="bell">🔔${unread ? `<i class="dot">${unread}</i>` : ""}</button>
        <button class="icon-btn" id="gear">⚙️</button>
      </div>

      <!-- 2.2 Hero (AI recommendation) -->
      <div class="hero fadein delay-1" style="background:linear-gradient(135deg, ${hero.color}, #ff6ba6)">
        <div class="tag">✨ Recommended for you</div>
        <div class="hero-row">
          <div class="hero-ico">${hero.icon}</div>
          <div><h3>${UI.esc(hero.title)}</h3><p>${UI.esc(hero.subtitle)}</p></div>
        </div>
        <button class="play" id="heroCta">${heroCtaIcon(hero.kind)} ${UI.esc(hero.cta)}</button>
      </div>

      <!-- 2.3 Continue journey -->
      ${cont ? `
      <div class="section fadein delay-1">
        <div class="section-h"><h3>▶ Continue your journey</h3><span class="muted" style="font-size:12px">${cont.progress}%</span></div>
        <div class="continue-card" id="contCard">
          <div class="cc-emoji" style="background:linear-gradient(135deg, ${cont.color}, rgba(11,7,32,.4))">${cont.world_emoji}</div>
          <div class="cc-body">
            <small>${UI.esc(cont.world_name)} · Mission</small>
            <b>${cont.mission_emoji} ${UI.esc(cont.mission_title)}</b>
            <div class="bar"><i style="width:${cont.progress}%"></i></div>
          </div>
          <div class="cc-play">▶</div>
        </div>
      </div>` : ""}

      <!-- 2.4 Learning worlds -->
      <div class="section fadein delay-2">
        <div class="section-h"><h3>🌌 Learning Worlds</h3><a id="seeworlds">See all</a></div>
        <div class="rail">${hp.worlds.map(worldCard).join("")}</div>
      </div>

      <!-- 2.5 Quick learn -->
      <div class="section fadein delay-2">
        <div class="section-h"><h3>⚡ Quick Learn</h3><span class="muted" style="font-size:12px">swipe →</span></div>
        <div class="rail">${hp.quick_learn.map((q, i) => `
          <div class="reel" data-ql="${i}">
            <div class="q">${q.q}</div>
            <div class="go">${q.go} →</div>
          </div>`).join("")}</div>
      </div>

      <!-- 2.6 Daily quests -->
      <div class="section fadein delay-3">
        <div class="section-h"><h3>🔥 Daily Quests</h3><span class="pill">🔥 ${hp.stats.streak} day streak</span></div>
        <div class="stack">${hp.daily_quests.map(questRow).join("")}</div>
      </div>

      <!-- 2.7 Memory shortcut -->
      <div class="section fadein delay-3">
        <div class="section-h"><h3>🧬 Your Memory</h3><a id="seemem">Open timeline</a></div>
        <div class="memcard" id="memCard">
          <div class="mtitle">${hp.memory.recent
            ? "You learned " + hp.memory.recent.emoji + " " + UI.esc(hp.memory.recent.title) + " " + ago(hp.memory.recent.learned_at)
            : "Your brain archive starts here 🧠"}</div>
          <div class="mstrength"><i style="width:${hp.memory.strength}%"></i></div>
          <div class="row" style="justify-content:space-between;align-items:center">
            <span class="muted" style="font-size:13px">${hp.memory.due_count
              ? hp.memory.due_count + " concept" + (hp.memory.due_count > 1 ? "s" : "") + " want a revision"
              : "Everything's fresh! 🔥"}</span>
            ${hp.memory.recent ? `<button class="pill" id="reviseShortcut">⚡ Revise</button>` : ""}
          </div>
        </div>
      </div>

      <!-- 2.8 Progress + level tier -->
      <div class="section fadein delay-4">
        <div class="section-h"><h3>📊 Progress</h3><a id="seeStats">Details</a></div>
        <div class="levelcard" id="levelCard">
          <div class="lc-top">
            <span class="lc-tier">${hp.level.tier.emoji} ${hp.level.tier.name}</span>
            ${hp.level.next_tier ? `<span class="muted" style="font-size:12px">${hp.level.next_tier.emoji} ${hp.level.next_tier.name}</span>` : `<span class="muted" style="font-size:12px">Max tier 👑</span>`}
          </div>
          <div class="lc-bar"><i style="width:${hp.level.progress}%"></i></div>
          <div class="lc-nudge">🤖 ${UI.esc(hp.level.nudge)}</div>
        </div>
        <div class="tiles" id="statTiles" style="margin-top:10px">
          <div class="tile"><b>🪙 ${hp.coins}</b><span>coins</span></div>
          <div class="tile"><b>${hp.stats.concepts}</b><span>concepts</span></div>
          <div class="tile"><b>${hp.memory.strength}%</b><span>memory 🧠</span></div>
        </div>
      </div>

      ${tabbar("home")}
    `);

    // wiring
    document.getElementById("toProfile").onclick = renderProfile;
    document.getElementById("bell").onclick = openNotifications;
    document.getElementById("gear").onclick = renderSettings;
    document.getElementById("heroCta").onclick = () => runHero(hero);
    const cc = document.getElementById("contCard");
    if (cc && cont) cc.onclick = () => openWorldMission(cont.world_id, cont.mission_id);
    document.getElementById("seeworlds").onclick = renderWorlds;
    document.getElementById("seemem").onclick = renderMemory;
    document.getElementById("seeStats").onclick = openAnalytics;
    const rs = document.getElementById("reviseShortcut");
    if (rs) rs.onclick = (e) => { e.stopPropagation(); reviseScope("needs_revision"); };
    document.getElementById("memCard").onclick = renderMemory;
    document.getElementById("levelCard").onclick = openAnalytics;
    document.querySelectorAll("[data-world]").forEach((el) => el.onclick = () => openWorld(el.dataset.world));
    document.querySelectorAll("[data-ql]").forEach((el) => el.onclick = () => openQuickLearn(+el.dataset.ql));
    wireTabs();

    // 5.10 reward feedback: celebrate freshly-earned achievements
    if (hp.new_achievements && hp.new_achievements.length) {
      UI.confetti();
      UI.toast(`🏅 ${hp.new_achievements.length} new achievement${hp.new_achievements.length > 1 ? "s" : ""} unlocked!`);
    }
  }

  function heroCtaIcon(kind) {
    return { continue_mission: "▶", new_world: "🚀", revise: "⚡", quick_learn: "💡" }[kind] || "▶";
  }
  function runHero(hero) {
    if (hero.kind === "revise") return reviseScope("needs_revision");
    if (hero.kind === "quick_learn") return openQuickLearn(0);
    if (hero.world_id && hero.mission_id) return openWorldMission(hero.world_id, hero.mission_id);
    UI.toast("Pick a world to begin!");
  }

  function worldCard(w) {
    const locked = !w.unlocked;
    return `
      <div class="world ${locked ? "locked" : ""}" data-world="${w.id}"
           style="background:linear-gradient(160deg, ${w.color}, rgba(11,7,32,.65))">
        ${w.recommended ? `<span class="wbadge">★ For you</span>` : ""}
        ${locked ? `<span class="wlock">🔒</span>` : ""}
        <div class="wemoji">${w.emoji}</div>
        <div>
          <h4>${UI.esc(w.name)}</h4>
          <small>Lv ${w.level} · ${w.done}/${w.total}</small>
          <div class="bar"><i style="width:${w.progress}%"></i></div>
        </div>
      </div>`;
  }

  function questRow(q) {
    const pct = Math.round((q.progress / q.target) * 100);
    return `
      <div class="quest ${q.done ? "done" : ""}">
        <div class="qi">${q.done ? "✅" : q.icon}</div>
        <div class="qt">
          <b>${UI.esc(q.label)}</b>
          <div class="qbar"><i style="width:${pct}%"></i></div>
        </div>
        <div class="qx">${q.done ? "✓" : "+" + q.reward}</div>
      </div>`;
  }

  /* ============ QUICK LEARN (micro-learning) ============ */
  function openQuickLearn(i) {
    const items = hp.quick_learn;
    if (!items.length) return;
    i = ((i % items.length) + items.length) % items.length;
    const q = items[i];
    // Count the view toward the daily quest (fire-and-forget).
    API.quickLearn({ user_id: App.userId(), id: q.id, title: cleanTitle(q.q), subject: q.subject, emoji: emojiOf(q.q), save: false }).catch(() => {});
    UI.render(`
      <div class="home-head"><button class="pill" onclick="Home._tab('home')">←</button>
        <div class="who"><h2>⚡ Quick Learn</h2><p>${i + 1} of ${items.length} · ${UI.esc(q.subject)}</p></div></div>
      <div class="ql-card fadein delay-1">
        <div class="ql-big">${emojiOf(q.q)}</div>
        <h2>${UI.esc(cleanTitle(q.q))}</h2>
        <p class="muted">A 60-second brain snack. Save it and it lives in your timeline forever.</p>
      </div>
      <div class="cta-bar stack fadein delay-2">
        <button class="btn btn--block" id="qlSave">🧠 Save to my brain</button>
        <div class="row">
          <button class="btn btn--ghost" style="flex:1" id="qlPrev">← Prev</button>
          <button class="btn btn--ghost" style="flex:1" id="qlNext">Next →</button>
        </div>
      </div>
      ${tabbar("home")}
    `);
    document.getElementById("qlSave").onclick = async () => {
      try {
        const r = await API.quickLearn({ user_id: App.userId(), id: q.id, title: cleanTitle(q.q), subject: q.subject, emoji: emojiOf(q.q), save: true });
        UI.toast(r.saved ? "🧠 Saved to your timeline!" : "Already in your brain ✨");
        await refresh();
      } catch (e) { UI.toast("Couldn't save — try again"); }
    };
    document.getElementById("qlPrev").onclick = () => openQuickLearn(i - 1);
    document.getElementById("qlNext").onclick = () => openQuickLearn(i + 1);
    wireTabs();
  }
  const cleanTitle = (s) => s.replace(/\s*[\p{Emoji_Presentation}\p{Extended_Pictographic}]+\s*$/u, "").trim();
  const emojiOf = (s) => { const m = s.match(/[\p{Emoji_Presentation}\p{Extended_Pictographic}]/gu); return m ? m[m.length - 1] : "⚡"; };

  /* ================= WORLDS ================= */
  function renderWorlds() {
    tab = "worlds";
    UI.render(`
      <div class="home-head fadein"><div class="who"><h2>🌌 Learning Worlds</h2><p>Choose your next adventure</p></div></div>
      <div class="stack fadein delay-1" style="margin-top:8px">
        ${hp.worlds.map((w) => `
          <div class="world wide ${w.unlocked ? "" : "locked"}" data-world="${w.id}"
               style="background:linear-gradient(120deg, ${w.color}, rgba(11,7,32,.6))">
            <div class="wemoji">${w.emoji}</div>
            <div style="flex:1">
              <h4>${UI.esc(w.name)} ${w.recommended ? "★" : ""}</h4>
              <small>${UI.esc(w.tagline)}</small>
              <div class="bar"><i style="width:${w.progress}%"></i></div>
            </div>
            <div style="font-size:22px">${w.unlocked ? "→" : "🔒"}</div>
          </div>`).join("")}
      </div>
      ${tabbar("worlds")}
    `);
    document.querySelectorAll("[data-world]").forEach((el) => el.onclick = () => openWorld(el.dataset.world));
    wireTabs();
  }

  function openWorld(id) {
    const hw = hpWorld(id);
    if (hw && !hw.unlocked) { UI.toast("🔒 Keep learning to unlock this world!"); return; }
    const w = worldById(id);
    if (!w) return;
    // mastery by concept title (from the timeline)
    const learned = {};
    tl.years.forEach((y) => y.concepts.forEach((c) => { if (c.world === w.name) learned[c.title] = c.mastery; }));

    // group missions into chapters (World → Chapter → Mission)
    const chapters = [];
    w.missions.forEach((m, i) => {
      const name = m.chapter || "Missions";
      let ch = chapters.find((c) => c.name === name);
      if (!ch) { ch = { name, items: [] }; chapters.push(ch); }
      ch.items.push({ ...m, n: i + 1 });
    });

    UI.render(`
      <div class="home-head fadein">
        <button class="pill" onclick="Home._back()">←</button>
        <div class="who"><h2>${w.emoji} ${UI.esc(w.name)}</h2><p>${UI.esc(w.tagline)}</p></div>
      </div>
      ${chapters.map((ch, ci) => `
        <div class="section ${ci === 0 ? "fadein delay-1" : "fadein delay-2"}">
          <div class="chapter-h"><span class="chapter-dot"></span><b>Chapter ${ci + 1}: ${UI.esc(ch.name)}</b></div>
          <div class="stack">
            ${ch.items.map((m) => {
              const mastery = learned[m.concept];
              const done = mastery != null;
              return `
              <div class="quest mrow" data-m="${m.id}" style="cursor:pointer">
                <div class="qi">${done ? "✅" : m.emoji}</div>
                <div class="qt"><b>Mission ${m.n}: ${UI.esc(m.title)}</b>
                  <span>${done ? levelLabel(mastery) + " · " + mastery + "% mastery" : "Learn: " + UI.esc(m.concept)}</span></div>
                ${done ? `<button class="pill mrevise" data-rm="${m.id}">⚡60s</button>` : `<div class="qx">▶</div>`}
              </div>`;
            }).join("")}
          </div>
        </div>`).join("")}
      ${tabbar("worlds")}
    `);
    document.querySelectorAll(".mrow").forEach((el) => el.onclick = () => playMission(w.id, el.dataset.m));
    document.querySelectorAll(".mrevise").forEach((el) => el.onclick = (e) => {
      e.stopPropagation(); Mission.revise(w.id, el.dataset.rm);
    });
    wireTabs();
  }

  function levelLabel(m) {
    if (m >= 81) return "Mastery"; if (m >= 51) return "Application";
    if (m >= 26) return "Understanding"; return "Discovery";
  }

  // Jump straight into a specific mission (from hero / continue card).
  function openWorldMission(worldId, missionId) {
    const hw = hpWorld(worldId);
    if (hw && !hw.unlocked) { UI.toast("🔒 Keep learning to unlock this world!"); return; }
    const w = worldById(worldId);
    const m = w && w.missions.find((x) => x.id === missionId);
    if (m) playMission(worldId, missionId, m.title, m.emoji);
    else openWorld(worldId);
  }

  /* ============ PLAY MISSION ============ */
  // The full Story→Game→Quiz→AI→Reward flow lives in Mission (mission.js).
  function playMission(worldId, missionId) {
    Mission.play(worldId, missionId);
  }

  /* ================= MEMORY / TIMELINE ================= */
  function renderMemory() {
    tab = "memory";
    const empty = tl.total_concepts === 0;
    const ret = tl.retention_label || "Strong";
    const retClass = ret === "Strong" ? "ok" : ret === "Medium" ? "mid" : "low";
    UI.render(`
      <div class="home-head fadein"><div class="who"><h2>🧬 Your Memory</h2><p>Google for your own brain 🔍</p></div></div>

      <!-- 4.7 brain meter -->
      <div class="brainmeter fadein delay-1">
        <div class="bm-ring" style="--pct:${tl.memory_strength}"><span>${tl.memory_strength}%</span></div>
        <div class="bm-info">
          <b>Memory strength: <span class="ret ${retClass}">${ret}</span></b>
          <div class="row" style="gap:8px;margin-top:8px;flex-wrap:wrap">
            <span class="pill">📚 ${tl.total_concepts} learned</span>
            <span class="pill">🏆 ${tl.mastered} mastered</span>
            <span class="pill">🔁 ${tl.revisions} revised</span>
          </div>
        </div>
      </div>

      <!-- 4.4 search your brain -->
      <div class="searchbar fadein delay-1" style="margin-top:14px">
        <input id="brainq" placeholder="🔍 Search anything you learned…" />
      </div>

      <!-- 4.5 instant revision modes -->
      <div class="section-h fadein delay-2"><h3>⚡ Revise</h3></div>
      <div class="rev-modes fadein delay-2">
        <button class="rev-mode" data-s="quick"><span>⚡</span><b>Quick</b><small>60-sec recent</small></button>
        <button class="rev-mode" data-s="smart"><span>🧠</span><b>Smart</b><small>weak spots</small></button>
        <button class="rev-mode" data-s="full"><span>🌍</span><b>Full</b><small>everything</small></button>
        <button class="rev-mode chal" data-s="challenge"><span>🔥</span><b>Challenge</b><small>hard mode</small></button>
      </div>

      <!-- 4.8 badges -->
      <div class="section-h fadein delay-2" style="margin-top:18px"><h3>🏅 Badges</h3></div>
      <div class="rail fadein delay-2">
        ${tl.badges.map((b) => `
          <div class="badge ${b.earned ? "earned" : ""}">
            <div class="bemoji">${b.icon}</div><b>${UI.esc(b.label)}</b>
            <small>${b.earned ? "Unlocked" : UI.esc(b.hint)}</small>
          </div>`).join("")}
      </div>

      <!-- 4.2 timeline -->
      <div class="section-h fadein delay-3" style="margin-top:18px"><h3>📅 Timeline</h3></div>
      <div id="tlbody" class="fadein delay-3">
        ${empty ? emptyState() : tl.years.map(yearBlock).join("")}
      </div>
      ${tabbar("memory")}
    `);
    const q = document.getElementById("brainq");
    q.addEventListener("input", debounce(async () => {
      const term = q.value.trim();
      const body = document.getElementById("tlbody");
      if (!term) { body.innerHTML = tl.years.map(yearBlock).join("") || emptyState(); wireConceptCards(); return; }
      const r = await API.searchBrain(App.userId(), term);
      body.innerHTML = r.results.length
        ? `<div class="muted" style="margin:6px 0 10px">${r.results.length} memories for "${UI.esc(term)}"</div>` + r.results.map(conceptRow).join("")
        : `<div class="empty"><span class="em">🔍</span>No memory of "${UI.esc(term)}" yet.<br>Go learn it!</div>`;
      wireConceptCards();
    }, 220));
    document.querySelectorAll(".rev-mode").forEach((b) => b.onclick = () => reviseScope(b.dataset.s));
    wireConceptCards();
    wireTabs();
  }

  function wireConceptCards() {
    document.querySelectorAll("[data-cid]").forEach((el) => el.onclick = () => openMemoryCard(+el.dataset.cid));
  }

  function yearBlock(y) {
    return `<div class="year">
      <div class="yh"><b>${y.year}</b><span>${y.count} concept${y.count > 1 ? "s" : ""}</span></div>
      ${y.months.map((m) => `
        <div class="month-h">${UI.esc(m.label)}</div>
        ${m.concepts.map(conceptRow).join("")}`).join("")}
    </div>`;
  }
  function conceptRow(c) {
    return `<div class="cmcard" data-cid="${c.id}">
      <div class="ce">${c.emoji || "✨"}</div>
      <div class="ci"><b>${UI.esc(c.title)}</b><span>${UI.esc(c.learned_via || c.subject)} · ${ago(c.learned_at)}</span></div>
      <div class="cm ${c.memory_strength < 60 ? "low" : ""}">${c.memory_strength}%</div>
    </div>`;
  }
  function emptyState() {
    return `<div class="empty"><span class="em">🧠</span><b>Your brain archive is empty… for now.</b><br>
      Complete a mission and watch it appear here forever.</div>`;
  }

  /* ================= 4.3 MEMORY CARD ================= */
  async function openMemoryCard(cid) {
    let d;
    try { d = await API.conceptCard(App.userId(), cid); }
    catch (e) { UI.toast("Couldn't open memory"); return; }
    const c = d.card;
    const retClass = c.retention === "Strong" ? "ok" : c.retention === "Medium" ? "mid" : "low";
    const methods = (c.method || []).filter((m) => m !== "play");
    UI.render(`
      <div class="home-head fadein"><button class="pill" onclick="Home._tab('memory')">←</button>
        <div class="who"><h2>Memory Card</h2><p>${UI.esc(c.subject || "")}</p></div></div>
      <div class="memcard-full fadein delay-1">
        <div class="mc-emoji">${c.emoji}</div>
        <h1 class="title center" style="margin:6px 0 2px">${UI.esc(c.title)}</h1>
        <p class="muted center" style="margin:0">${UI.esc(d.smart_recall)}</p>
        <div class="mc-bar"><i style="width:${c.memory_strength}%"></i></div>
        <div class="row center" style="justify-content:center;gap:8px;margin-top:4px">
          <span class="ret ${retClass}">${c.retention}</span>
          <span class="muted" style="font-size:13px">${c.mastery}% mastery · revised ${c.revision_count}×</span>
        </div>
        ${methods.length ? `<div class="row" style="justify-content:center;gap:6px;flex-wrap:wrap;margin-top:10px">
          ${methods.map((m) => `<span class="pill">${methodEmoji(m)} ${UI.esc(m)}</span>`).join("")}</div>` : ""}
      </div>
      <div class="bubble fadein delay-2" style="margin-top:14px">${UI.esc(d.action.text)}</div>
      <div class="cta-bar stack fadein delay-2">
        <button class="btn btn--block" id="mcRevise">▶ Revise this</button>
        <div class="row">
          <button class="btn btn--ghost" style="flex:1" id="mcReplay">🔁 Replay</button>
          <button class="btn btn--ghost" style="flex:1" id="mcAsk">🧠 Ask AI</button>
        </div>
      </div>
      ${tabbar("memory")}
    `);
    document.getElementById("mcRevise").onclick = async () => {
      const r = await API.reviseConcept(App.userId(), cid);
      await refresh();
      runFlashcards([r.card], 0);
    };
    document.getElementById("mcReplay").onclick = () => {
      const w = worlds.find((x) => x.missions.some((m) => m.concept === c.title));
      const m = w && w.missions.find((x) => x.concept === c.title);
      if (w && m) Mission.replay(w.id, m.id);
      else UI.toast("This one came from Quick Learn — no mission to replay 🙂");
    };
    document.getElementById("mcAsk").onclick = () =>
      Mentor.open(`Explain "${c.title}" to me in a brand new fun way, different from before.`);
    wireTabs();
  }
  function methodEmoji(m) { return { story: "📖", game: "🎮", quiz: "🧠", quick_learn: "⚡", match: "🔗", slider: "🎚️", order: "🔢", choose: "🌿" }[m] || "✨"; }

  /* ================= REVISION ================= */
  async function reviseScope(scope) {
    const r = await API.revise(App.userId(), scope);
    if (!r.count) { UI.toast(scope === "smart" ? "Nothing needs revising — great memory! 🔥" : "Nothing to revise here yet!"); return; }
    runFlashcards(r.cards, 0);
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

  /* ================= NOTIFICATIONS ================= */
  function openNotifications() {
    const items = hp.notifications || [];
    const sheet = UI.h(`
      <div class="sheet"><div class="scrim"></div>
        <div class="panel">
          <div class="phead"><b>🔔 Notifications</b>${items.length ? `<button class="pill" id="readAll" style="margin-left:auto;margin-right:8px">Mark all read</button>` : ""}<button class="close">✕</button></div>
          <div class="stack" style="padding:16px;max-height:60vh;overflow:auto">
            ${items.length ? items.map((n) => `
              <div class="quest"><div class="qi">${n.icon}</div><div class="qt"><b>${UI.esc(n.text)}</b><span>${UI.esc(n.type)}</span></div></div>`).join("")
              : `<div class="empty"><span class="em">🎉</span>You're all caught up!</div>`}
          </div>
        </div></div>`);
    document.querySelector(".stage").appendChild(sheet);
    const close = () => sheet.remove();
    sheet.querySelector(".scrim").onclick = close;
    sheet.querySelector(".close").onclick = close;
    const ra = sheet.querySelector("#readAll");
    if (ra) ra.onclick = () => { items.forEach((n) => dismissed.add(n.id)); close(); renderHome(); };
  }

  /* ================= ANALYTICS (progress details) ================= */
  function openAnalytics() {
    const s = hp.stats;
    const interests = (me.interests || []).join(", ") || "exploring";
    const sheet = UI.h(`
      <div class="sheet"><div class="scrim"></div>
        <div class="panel">
          <div class="phead"><b>📊 Your Progress</b><button class="close">✕</button></div>
          <div style="padding:16px;max-height:74vh;overflow:auto">
            <div class="tiles" style="margin-bottom:12px">
              <div class="tile"><b>${s.xp}</b><span>total XP</span></div>
              <div class="tile"><b>${s.level}</b><span>level</span></div>
              <div class="tile"><b>${s.streak}</b><span>day streak</span></div>
            </div>
            <div class="tiles" style="margin-bottom:12px">
              <div class="tile"><b>${s.concepts}</b><span>concepts</span></div>
              <div class="tile"><b>${s.mastered}</b><span>mastered</span></div>
              <div class="tile"><b>${hp.memory.strength}%</b><span>memory 🧠</span></div>
            </div>
            <div class="section-h"><h3>Worlds explored</h3></div>
            <div class="stack">${hp.worlds.map((w) => `
              <div class="quest"><div class="qi">${w.emoji}</div><div class="qt"><b>${UI.esc(w.name)}</b>
                <div class="qbar"><i style="width:${w.progress}%"></i></div></div><div class="qx">${w.progress}%</div></div>`).join("")}</div>
            <div class="section-h" style="margin-top:16px"><h3>AI insight</h3></div>
            <div class="bubble">${UI.esc(me.name)} loves <b>${UI.esc(interests)}</b> and is building strong curiosity. Keep the daily streak alive for compounding growth 🔥</div>
          </div>
        </div></div>`);
    document.querySelector(".stage").appendChild(sheet);
    const close = () => sheet.remove();
    sheet.querySelector(".scrim").onclick = close;
    sheet.querySelector(".close").onclick = close;
  }

  /* ================= PROFILE ================= */
  function renderProfile() {
    tab = "profile";
    const interests = me.interests || [];
    UI.render(`
      <div class="home-head fadein"><div class="who"><h2>👤 Profile</h2><p>Your hero & settings</p></div></div>
      <div class="profile-hero fadein delay-1">
        <div class="mascot">${me.avatar.emoji || "🦊"}</div>
        <h2 style="margin:6px 0 2px">${UI.esc(me.name)}</h2>
        <div class="row" style="justify-content:center;gap:6px;margin:4px 0">
          <span class="tierbadge">${hp.level.tier.emoji} ${hp.level.tier.name}</span>
          <span class="coinchip">🪙 ${hp.coins}</span>
          <span class="pill">🔥 ${hp.stats.streak}</span>
        </div>
        <div class="lc-bar" style="max-width:240px;margin:8px auto 0"><i style="width:${hp.level.progress}%"></i></div>
        <p class="muted" style="margin:6px 0 0;font-size:12px">${hp.stats.xp} XP · ${UI.esc(hp.level.nudge)}</p>
        <div class="row" style="flex-wrap:wrap;justify-content:center;gap:6px;margin-top:10px">
          ${interests.map((i) => `<span class="pill">${UI.esc(i)}</span>`).join("") || `<span class="muted">No interests yet</span>`}
        </div>
      </div>
      <div class="stack fadein delay-2" style="margin-top:16px">
        <button class="quest" id="pShop" style="text-align:left"><div class="qi">🛍️</div><div class="qt"><b>Avatar Shop</b><span>Spend coins on new looks</span></div><div class="qx">🪙 ${hp.coins}</div></button>
        <button class="quest" id="pAch" style="text-align:left"><div class="qi">🏅</div><div class="qt"><b>Achievements</b><span>Your unlocked badges</span></div><div class="qx">→</div></button>
        <button class="quest" id="pEdit" style="text-align:left"><div class="qi">🎭</div><div class="qt"><b>Edit avatar</b><span>Change your hero look</span></div><div class="qx">→</div></button>
        <button class="quest" id="pSettings" style="text-align:left"><div class="qi">⚙️</div><div class="qt"><b>Settings</b><span>Language, mentor vibe, voice</span></div><div class="qx">→</div></button>
        <button class="quest" id="pParent" style="text-align:left"><div class="qi">👨‍👩‍👧</div><div class="qt"><b>Parent Zone</b><span>Reports & growth story (PIN)</span></div><div class="qx">→</div></button>
        <button class="quest" id="pReset" style="text-align:left"><div class="qi">🔄</div><div class="qt"><b>Reset demo</b><span>Start over from onboarding</span></div><div class="qx">→</div></button>
      </div>
      ${tabbar("profile")}
    `);
    document.getElementById("pShop").onclick = renderShop;
    document.getElementById("pAch").onclick = renderAchievements;
    document.getElementById("pEdit").onclick = openAvatarSheet;
    document.getElementById("pSettings").onclick = renderSettings;
    document.getElementById("pParent").onclick = parentGate;
    document.getElementById("pReset").onclick = () => { App.clear(); App.welcome(); };
    wireTabs();
  }

  /* ================= 5.6 AVATAR SHOP ================= */
  async function renderShop() {
    tab = "profile";
    let d;
    try { d = await API.shop(App.userId()); }
    catch (e) { UI.toast("Couldn't load shop"); return renderProfile(); }
    UI.render(`
      <div class="home-head fadein"><button class="pill" onclick="Home._tab('profile')">←</button>
        <div class="who"><h2>🛍️ Avatar Shop</h2><p>Spend coins, unlock heroes</p></div>
        <span class="coinchip">🪙 ${d.coins}</span></div>
      <div class="shop-grid fadein delay-1">
        ${d.items.map((it) => {
          const state = it.owned ? "owned" : it.tier_locked ? "tier" : it.affordable ? "buy" : "poor";
          return `
          <div class="shop-item ${state}" data-buy="${it.id}" data-emoji="${it.emoji}" data-state="${state}">
            <div class="si-emoji">${it.emoji}</div>
            <b>${UI.esc(it.name)}</b>
            <span class="si-cost">${
              it.owned ? (d.equipped === it.emoji ? "✓ Equipped" : "Tap to equip")
              : it.tier_locked ? `🔒 ${it.tier_name}`
              : `🪙 ${it.cost}`}</span>
          </div>`;
        }).join("")}
      </div>
      ${tabbar("profile")}
    `);
    document.querySelectorAll("[data-buy]").forEach((el) => el.onclick = async () => {
      const id = el.dataset.buy, state = el.dataset.state;
      if (state === "owned") {       // equip
        await API.updatePrefs(App.userId(), { avatar: { ...me.avatar, emoji: el.dataset.emoji } });
        me.avatar.emoji = el.dataset.emoji; UI.toast("Equipped! 🦸"); renderShop(); return;
      }
      if (state === "tier") { UI.toast("🔒 Reach a higher tier to unlock this!"); return; }
      if (state === "poor") { UI.toast("Not enough coins — keep learning! 🪙"); return; }
      try {
        const r = await API.buyItem(App.userId(), id);
        me.avatar.emoji = r.equipped;
        UI.confetti(); UI.toast(`Unlocked & equipped! 🪙 ${r.coins} left`);
        await refresh(); renderShop();
      } catch (e) { UI.toast("Purchase failed"); }
    });
    wireTabs();
  }

  /* ================= 5.7 ACHIEVEMENTS ================= */
  async function renderAchievements() {
    tab = "profile";
    let d;
    try { d = await API.achievements(App.userId()); }
    catch (e) { UI.toast("Couldn't load achievements"); return renderProfile(); }
    UI.render(`
      <div class="home-head fadein"><button class="pill" onclick="Home._tab('profile')">←</button>
        <div class="who"><h2>🏅 Achievements</h2><p>${d.earned} of ${d.total} unlocked</p></div></div>
      <div class="ach-grid fadein delay-1">
        ${d.items.map((a) => `
          <div class="ach ${a.earned ? "earned" : ""}">
            <div class="ach-ico">${a.icon}</div>
            <b>${UI.esc(a.name)}</b>
            <small>${a.earned ? "✓ Unlocked" : UI.esc(a.desc)}</small>
          </div>`).join("")}
      </div>
      ${tabbar("profile")}
    `);
    wireTabs();
  }

  function openAvatarSheet() {
    const list = (window.DATA && window.DATA.avatars) || ["🦊","🐯","🐼","🚀","🦄","🤖"];
    const sheet = UI.h(`
      <div class="sheet"><div class="scrim"></div>
        <div class="panel">
          <div class="phead"><b>🎭 Choose your hero</b><button class="close">✕</button></div>
          <div class="choices grid-3" style="padding:16px">
            ${list.map((e) => `<button class="choice ${me.avatar.emoji === e ? "selected" : ""}" data-e="${e}" style="font-size:30px;padding:14px">${e}</button>`).join("")}
          </div>
        </div></div>`);
    document.querySelector(".stage").appendChild(sheet);
    const close = () => sheet.remove();
    sheet.querySelector(".scrim").onclick = close;
    sheet.querySelector(".close").onclick = close;
    sheet.querySelectorAll("[data-e]").forEach((b) => b.onclick = async () => {
      const e = b.dataset.e;
      try {
        await API.updatePrefs(App.userId(), { avatar: { ...me.avatar, emoji: e } });
        me.avatar.emoji = e;
        close(); UI.toast("Hero updated! 🦸"); renderProfile();
      } catch (_) { UI.toast("Couldn't save"); }
    });
  }

  /* ================= SETTINGS ================= */
  function renderSettings() {
    tab = "profile";
    const D = window.DATA;
    UI.render(`
      <div class="home-head fadein"><button class="pill" onclick="Home._tab('profile')">←</button>
        <div class="who"><h2>⚙️ Settings</h2><p>Make Wolio yours</p></div></div>

      <div class="section fadein delay-1"><div class="section-h"><h3>Language</h3></div>
        <div class="choices grid-3" id="setLang">
          ${D.languages.map((l) => `<button class="choice ${me.language === l.id ? "selected" : ""}" data-id="${l.id}"><span class="emoji">${l.emoji}</span>${l.label}</button>`).join("")}
        </div>
      </div>
      <div class="section fadein delay-2"><div class="section-h"><h3>Mentor vibe</h3></div>
        <div class="choices grid-3" id="setTone">
          ${D.tones.map((t) => `<button class="choice ${me.tone === t.id ? "selected" : ""}" data-id="${t.id}"><span class="emoji">${t.emoji}</span>${t.label}</button>`).join("")}
        </div>
      </div>
      <div class="section fadein delay-3">
        <div class="quest"><div class="qi">🔊</div><div class="qt"><b>Voice replies</b><span>Hear your mentor talk</span></div>
          <button class="pill" id="setVoice">${me.voice ? "On" : "Off"}</button></div>
      </div>
      ${tabbar("profile")}
    `);
    document.querySelectorAll("#setLang .choice").forEach((b) => b.onclick = () => savePref("language", b.dataset.id, "setLang", b));
    document.querySelectorAll("#setTone .choice").forEach((b) => b.onclick = () => savePref("tone", b.dataset.id, "setTone", b));
    document.getElementById("setVoice").onclick = async (e) => {
      const v = !me.voice;
      try { await API.updatePrefs(App.userId(), { voice: v }); me.voice = v; e.target.textContent = v ? "On" : "Off"; UI.toast("Saved ✓"); }
      catch (_) { UI.toast("Couldn't save"); }
    };
    wireTabs();
  }
  async function savePref(key, val, container, btn) {
    try {
      await API.updatePrefs(App.userId(), { [key]: val });
      me[key] = val;
      document.querySelectorAll(`#${container} .choice`).forEach((x) => x.classList.remove("selected"));
      btn.classList.add("selected");
      UI.toast("Saved ✓");
    } catch (_) { UI.toast("Couldn't save"); }
  }

  /* ================= PARENT ZONE ================= */
  function parentGate() {
    tab = "profile";
    let pin = "";
    UI.render(`
      <div class="home-head fadein"><button class="pill" onclick="Home._tab('profile')">←</button>
        <div class="who"><h2>👨‍👩‍👧 Parent Zone</h2><p>Enter PIN to view reports</p></div></div>
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
      ${tabbar("profile")}
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

  // The full parent dashboard lives in Parent (parent.js).
  function parentDashboard() { Parent.open(App.userId()); }

  /* ================= NAV ================= */
  function tabbar(active) {
    const items = [
      { id: "home", i: "🏠", t: "Home" },
      { id: "worlds", i: "🌌", t: "Worlds" },
      { id: "memory", i: "🧬", t: "Memory" },
      { id: "mentor", i: "🤖", t: "Mentor" },
      { id: "profile", i: "👤", t: "Profile" },
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
    else if (t === "mentor") Mentor.open();
    else if (t === "profile") renderProfile();
  }
  function _back() { _tab(tab === "mentor" ? "home" : tab); }

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

  return { enter, renderHome, parentGate, _tab, _back, getMe: () => me,
           tabbar, wireTabs, subjEmoji: (s) => ({ Science: "🔬", Math: "🧮", Literature: "📖", History: "⏳", Biology: "🌱", Physics: "🚀", Music: "🎵" }[s] || "📚") };
})();
