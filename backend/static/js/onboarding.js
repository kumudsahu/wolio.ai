/* Onboarding flow — Screens 1.1 → 1.9. Each screen = one decision. */
window.Onboarding = (function () {
  const TOTAL = 7; // visible step dots (name..mentor)
  let draft = {};
  let step = 0;

  function start() {
    draft = {
      name: "", age_group: "", grade: "", language: "hinglish", tone: "fun",
      voice: true, interests: [], learning_style: "games", avatar: { emoji: "🦊" },
      behavior: {},
    };
    step = 0;
    screenName();
  }

  const D = () => window.DATA;

  /* ---------- 1.1 Name ---------- */
  function screenName() {
    step = 0;
    UI.render(`
      ${UI.progressDots(step, TOTAL)}
      <div class="mascot" id="m">🦊</div>
      <h1 class="title center">Hey! What should I call you?</h1>
      <p class="subtitle center">Your AI buddy is excited to meet you ✨</p>
      <input class="field" id="name" placeholder="Type your name" maxlength="20"
             value="${UI.esc(draft.name)}" autocomplete="off" />
      <div class="cta-bar"><button class="btn btn--block" id="next" disabled>Continue →</button></div>
    `);
    const input = document.getElementById("name");
    const btn = document.getElementById("next");
    const m = document.getElementById("m");
    input.focus();
    input.addEventListener("input", () => {
      m.classList.remove("wave"); void m.offsetWidth; m.classList.add("wave");
      btn.disabled = input.value.trim().length < 2;
    });
    const go = () => {
      let n = input.value.trim();
      if (n.length < 2) return;
      draft.name = n.charAt(0).toUpperCase() + n.slice(1);
      screenAge();
    };
    btn.onclick = go;
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") go(); });
  }

  /* ---------- 1.2 Age + grade ---------- */
  function screenAge() {
    step = 1;
    UI.render(`
      ${UI.progressDots(step, TOTAL)}
      <h1 class="title">How old are you, ${UI.esc(draft.name)}?</h1>
      <p class="subtitle">This tunes everything to your level.</p>
      <div class="choices grid-2" id="ages">
        ${D().ages.map((a) => `
          <button class="choice ${draft.age_group === a.id ? "selected" : ""}" data-id="${a.id}">
            ${a.label}<span class="sub">${a.sub}</span>
          </button>`).join("")}
      </div>
      ${backNext("screenName", "next")}
    `);
    wireChoices("ages", (id) => { draft.age_group = id; enable("next"); });
    document.getElementById("next").onclick = () => draft.age_group && screenLanguage();
    if (draft.age_group) enable("next");
  }

  /* ---------- 1.3 Language ---------- */
  function screenLanguage() {
    step = 2;
    UI.render(`
      ${UI.progressDots(step, TOTAL)}
      <h1 class="title">Which language feels like home?</h1>
      <p class="subtitle">Your mentor will talk just like that.</p>
      <div class="choices" id="langs">
        ${D().languages.map((l) => `
          <button class="choice ${draft.language === l.id ? "selected" : ""}" data-id="${l.id}">
            <span class="emoji">${l.emoji}</span>${l.label}
          </button>`).join("")}
      </div>
      ${backNext("screenAge", "next")}
    `);
    wireChoices("langs", (id) => { draft.language = id; enable("next"); }, true);
    enable("next");
    document.getElementById("next").onclick = screenInterests;
  }

  /* ---------- 1.4 Interests (min 3) ---------- */
  function screenInterests() {
    step = 3;
    UI.render(`
      ${UI.progressDots(step, TOTAL)}
      <h1 class="title">What do you love? ❤️</h1>
      <p class="subtitle">Pick at least 3 — I'll build lessons around them.</p>
      <div class="choices grid-3" id="ints">
        ${D().interests.map((i) => `
          <button class="choice ${draft.interests.includes(i.id) ? "selected" : ""}" data-id="${i.id}">
            <span class="emoji">${i.emoji}</span><span style="font-size:13px">${i.label}</span>
          </button>`).join("")}
      </div>
      ${backNext("screenLanguage", "next")}
    `);
    const upd = () => { document.getElementById("next").disabled = draft.interests.length < 3; };
    document.querySelectorAll("#ints .choice").forEach((b) => {
      b.onclick = () => {
        const id = b.dataset.id;
        if (draft.interests.includes(id)) draft.interests = draft.interests.filter((x) => x !== id);
        else draft.interests.push(id);
        b.classList.toggle("selected");
        upd();
      };
    });
    upd();
    document.getElementById("next").onclick = () => draft.interests.length >= 3 && screenBehavior(0);
  }

  /* ---------- 1.5 Behavior mini-test ---------- */
  function screenBehavior(i) {
    step = 4;
    const task = D().behavior[i];
    UI.render(`
      ${UI.progressDots(step, TOTAL)}
      <span class="pill" style="margin:0 auto 14px">🔎 Quick game ${i + 1}/${D().behavior.length}</span>
      <div class="mascot sm" style="margin:0 auto 14px">${task.icon}</div>
      <h1 class="title center">${task.q}</h1>
      <div class="choices" id="bt" style="margin-top:8px">
        ${task.options.map((o, k) => `<button class="choice" data-v="${o.v}" data-k="${k}">${o.t}</button>`).join("")}
      </div>
    `);
    const t0 = performance.now();
    document.querySelectorAll("#bt .choice").forEach((b) => {
      b.onclick = () => {
        b.classList.add("selected");
        draft.behavior[task.id] = { value: b.dataset.v, ms: Math.round(performance.now() - t0) };
        setTimeout(() => {
          if (i + 1 < D().behavior.length) screenBehavior(i + 1);
          else screenAvatar();
        }, 280);
      };
    });
  }

  /* ---------- 1.6 Avatar — pick a Curio-Verse character ---------- */
  function screenAvatar() {
    step = 5;
    const cast = (D().crewAvatars || D().avatars.map((e) => ({ emoji: e, name: "" })));
    if (!draft.avatar.name) { draft.avatar.emoji = cast[0].emoji; draft.avatar.name = cast[0].name; }
    UI.render(`
      ${UI.progressDots(step, TOTAL)}
      <h1 class="title center">Pick your character 🦸</h1>
      <p class="subtitle center">This is who you'll be in the Curio-Verse!</p>
      <div class="mascot" id="preview">${draft.avatar.emoji}</div>
      <div class="choices grid-3" id="av" style="margin-top:6px">
        ${cast.map((c) => `<button class="choice ${draft.avatar.emoji === c.emoji ? "selected" : ""}" data-e="${c.emoji}" data-n="${UI.esc(c.name)}">
          <span class="emoji">${c.emoji}</span><span style="font-size:12px">${UI.esc(c.name)}</span></button>`).join("")}
      </div>
      ${backNext("screenInterestsBack", "next")}
    `);
    document.querySelectorAll("#av .choice").forEach((b) => {
      b.onclick = () => {
        document.querySelectorAll("#av .choice").forEach((x) => x.classList.remove("selected"));
        b.classList.add("selected");
        draft.avatar.emoji = b.dataset.e; draft.avatar.name = b.dataset.n;
        const p = document.getElementById("preview");
        p.textContent = b.dataset.e;
        p.classList.remove("wave"); void p.offsetWidth; p.classList.add("wave");
      };
    });
    enable("next");
    document.getElementById("next").onclick = screenMentor;
  }
  function screenInterestsBack() { screenInterests(); }

  /* ---------- 1.7 Mentor config ---------- */
  function screenMentor() {
    step = 6;
    UI.render(`
      ${UI.progressDots(step, TOTAL)}
      <div class="mascot" style="background:var(--grad-cta)">🤖</div>
      <div class="bubble center" style="margin-bottom:18px">I'll teach you in a way <b>YOU</b> love 😎</div>
      <h3 style="margin:0 0 10px">Pick my vibe</h3>
      <div class="choices grid-3" id="tones">
        ${D().tones.map((t) => `<button class="choice ${draft.tone === t.id ? "selected" : ""}" data-id="${t.id}"><span class="emoji">${t.emoji}</span>${t.label}</button>`).join("")}
      </div>
      <div class="quest" style="margin-top:16px">
        <div class="qi">🔊</div>
        <div class="qt"><b>Voice replies</b><span>Hear your mentor talk</span></div>
        <button class="pill" id="voice">${draft.voice ? "On" : "Off"}</button>
      </div>
      ${backNext("screenAvatar", "next", "Build my universe 🚀")}
    `);
    wireChoices("tones", (id) => { draft.tone = id; }, true);
    document.getElementById("voice").onclick = (e) => {
      draft.voice = !draft.voice; e.target.textContent = draft.voice ? "On" : "Off";
    };
    enable("next");
    document.getElementById("next").onclick = screenBuilding;
  }

  /* ---------- 1.8 Magic moment ---------- */
  async function screenBuilding() {
    UI.render(`
      <div class="builder">
        <div class="ring"></div>
        <h1 class="title center" style="margin:0">Building your universe…</h1>
        <p class="build-step" id="bs">Reading your interests…</p>
      </div>
    `);
    const steps = [
      "Reading your interests…",
      `Tuning lessons for age ${draft.age_group}…`,
      "Designing your first mission…",
      "Waking up your AI mentor…",
    ];
    let k = 0;
    const bs = document.getElementById("bs");
    const tick = setInterval(() => { k = (k + 1) % steps.length; bs.textContent = steps[k]; }, 700);

    try {
      const res = await API.onboarding({ ...draft, email: App.getEmail && App.getEmail() });
      App.setUser(res.user_id);
      setTimeout(() => { clearInterval(tick); screenFirstMission(res.journey); }, 1600);
    } catch (e) {
      clearInterval(tick);
      UI.toast("Hmm, something glitched. Retrying…");
      setTimeout(screenMentor, 800);
    }
  }

  /* ---------- 1.9 First mission preview ---------- */
  function screenFirstMission(journey) {
    const m = journey.first_mission;
    const w = journey.primary_world;
    UI.render(`
      <div class="center fadein">
        <span class="pill" style="margin:0 auto">✨ Magic moment</span>
        <div class="mascot" style="margin:18px auto 12px">${draft.avatar.emoji}</div>
        <h1 class="title">${UI.esc(journey.headline)}</h1>
        <p class="subtitle">${UI.esc(journey.pitch)}</p>
      </div>
      <div class="resume fadein delay-1" style="background:linear-gradient(135deg, ${w.color}, #ff6ba6)">
        <div class="tag">${w.emoji} ${UI.esc(w.name)} · Mission 1</div>
        <h3>${m.emoji} ${UI.esc(m.title)}</h3>
        <p>Your very first adventure is ready.</p>
        <span class="play">▶ Start mission</span>
      </div>
      <div class="cta-bar stack">
        <button class="btn btn--block" id="start">Let's go, ${UI.esc(draft.name)}! 🚀</button>
        <button class="btn btn--ghost btn--block" id="explore">Explore my universe instead</button>
      </div>
    `);
    document.getElementById("start").onclick = () => Home.enter({ playFirst: journey });
    document.getElementById("explore").onclick = () => Home.enter({});
  }

  /* ---------- helpers ---------- */
  function wireChoices(containerId, onPick, single) {
    document.querySelectorAll(`#${containerId} .choice`).forEach((b) => {
      b.onclick = () => {
        if (single) document.querySelectorAll(`#${containerId} .choice`).forEach((x) => x.classList.remove("selected"));
        b.classList.add("selected");
        onPick(b.dataset.id);
      };
    });
  }
  function enable(id) { const b = document.getElementById(id); if (b) b.disabled = false; }
  function backNext(backFn, nextId, nextLabel) {
    return `
      <div class="cta-bar row">
        <button class="btn btn--ghost" style="flex:0 0 64px" onclick="Onboarding._back('${backFn}')">←</button>
        <button class="btn" style="flex:1" id="${nextId}" disabled>${nextLabel || "Continue →"}</button>
      </div>`;
  }

  return {
    start,
    _back: (fn) => Onboarding[fn] ? Onboarding[fn]() : window[fn] && window[fn](),
    screenName, screenAge, screenLanguage, screenInterests, screenInterestsBack, screenAvatar, screenMentor,
  };
})();
