/* Mission player — the Learning World System core (Step 3).
   Flow: Story → Exploration → Game → Quiz → AI Explanation → Reward → Memory Save. */
window.Mission = (function () {
  let M = null;  // active mission run state

  const PHASES = ["Story", "Explore", "Game", "Quiz", "Learn", "Reward"];

  async function play(worldId, missionId, opts = {}) {
    const mode = opts.mode || "play";
    UI.render(`<div class="builder"><div class="ring"></div><p class="build-step">Loading mission…</p></div>`);
    let data;
    try {
      data = await API.missionGet(worldId, missionId, App.userId());
    } catch (e) { UI.toast("Couldn't load mission"); return Home.renderHome(); }

    M = {
      world: data.world, mission: data.mission, pb: data.playbook, mode,
      mastery: data.mastery, level: data.level,
      startTs: Date.now(), engagement: 0,
      quiz: { total: data.playbook.quiz.length, correct: 0, attempts: 0 },
    };
    if (mode === "revise") return pQuiz(0, true);  // 60-sec revision = quiz only
    pStory(0);
  }

  const replay = (w, m) => play(w, m, { mode: "replay" });
  const challenge = (w, m) => play(w, m, { mode: "challenge" });
  const revise = (w, m) => play(w, m, { mode: "revise" });

  /* ---------- phase chrome ---------- */
  function header(stepIdx) {
    const segs = PHASES.map((p, i) =>
      `<i class="${i < stepIdx ? "done" : i === stepIdx ? "active" : ""}"></i>`).join("");
    return `
      <div class="mhead">
        <button class="icon-btn" onclick="Mission._quit()">✕</button>
        <div class="mseg">${segs}</div>
        <div class="mscene">${M.world.emoji}</div>
      </div>`;
  }

  /* ---------- 3.3.1 STORY ---------- */
  function pStory(i) {
    const lines = M.pb.story;
    const line = lines[i];
    const last = i >= lines.length - 1;
    UI.render(`
      ${header(0)}
      <div class="story-scene" style="--scene-bg:${M.world.color}">
        <div class="scene-emoji">${M.pb.scene}</div>
      </div>
      <div class="story-box fadein">
        <div class="sp"><span class="sp-emoji">${line.emoji}</span><b>${UI.esc(line.who)}</b></div>
        <p class="sp-text">${UI.esc(line.text)}</p>
      </div>
      <div class="cta-bar"><button class="btn btn--block" id="next">${last ? "Start exploring 🔭" : "Next →"}</button></div>
    `);
    document.getElementById("next").onclick = () => last ? pExplore() : pStory(i + 1);
  }

  /* ---------- 3.3.2 EXPLORATION ---------- */
  function pExplore() {
    const ex = M.pb.exploration;
    const seen = new Set();
    UI.render(`
      ${header(1)}
      <h2 class="title" style="font-size:21px">${UI.esc(ex.prompt)}</h2>
      <div class="explore-grid">
        ${ex.items.map((it, k) => `
          <button class="exp-item" data-k="${k}">
            <span class="exp-emoji">${it.emoji}</span>
            <span class="exp-label">${UI.esc(it.label)}</span>
          </button>`).join("")}
      </div>
      <div class="exp-fact" id="fact">Tap above to discover ✨</div>
      <div class="cta-bar"><button class="btn btn--block" id="next" disabled>Explore a bit first…</button></div>
    `);
    const fact = document.getElementById("fact");
    const next = document.getElementById("next");
    document.querySelectorAll(".exp-item").forEach((b) => b.onclick = () => {
      const it = ex.items[+b.dataset.k];
      fact.textContent = it.fact; fact.classList.remove("pop"); void fact.offsetWidth; fact.classList.add("pop");
      b.classList.add("seen"); seen.add(b.dataset.k); M.engagement++;
      if (seen.size >= Math.min(2, ex.items.length)) { next.disabled = false; next.textContent = "To the challenge 🎮"; }
    });
    next.onclick = pGame;
  }

  /* ---------- 3.3.3 GAME (reusable engines) ---------- */
  function pGame() {
    const g = M.pb.game;
    const shell = (inner) => `${header(2)}<h2 class="title" style="font-size:20px">${UI.esc(g.prompt)}</h2>${inner}`;
    const win = () => { M.engagement++; UI.toast(g.success || "Nice!"); setTimeout(() => pQuiz(0), 650); };
    ({ slider: gameSlider, match: gameMatch, order: gameOrder, choose: gameChoose }[g.type] || gameChoose)(g, shell, win);
  }

  function gameSlider(g, shell, win) {
    const mid = Math.round((g.min + g.max) / 2);
    UI.render(shell(`
      <div class="sim fadein">
        <div class="sim-stage"><span class="sim-actor" id="actor">${g.emoji || "🎯"}</span></div>
        <div class="sim-read" id="read">${mid} ${g.unit || ""}</div>
        <input type="range" class="slider" id="sl" min="${g.min}" max="${g.max}" value="${mid}" />
        <div class="sim-feedback" id="fb">Drag the slider…</div>
      </div>
      <div class="cta-bar"><button class="btn btn--block" id="lock" disabled>Lock it in 🔒</button></div>
    `));
    const sl = document.getElementById("sl"), read = document.getElementById("read"),
          fb = document.getElementById("fb"), lock = document.getElementById("lock"), actor = document.getElementById("actor");
    const upd = () => {
      const v = +sl.value; read.textContent = `${v} ${g.unit || ""}`;
      const ok = Math.abs(v - g.target) <= g.tol;
      actor.style.transform = `translateY(${Math.max(-30, Math.min(30, (g.target - v) * 1.5))}px) scale(${ok ? 1.15 : 1})`;
      if (ok) { fb.textContent = "Perfect! 🎯"; fb.className = "sim-feedback ok"; lock.disabled = false; }
      else { fb.textContent = v < g.target ? g.low : g.high; fb.className = "sim-feedback"; lock.disabled = true; }
    };
    sl.oninput = () => { M.engagement++; upd(); };
    upd();
    lock.onclick = win;
  }

  function gameMatch(g, shell, win) {
    const order = g.pairs.map((_, i) => i);
    const rights = shuffle(order.slice());
    UI.render(shell(`
      <div class="match fadein">
        <div class="match-col">${g.pairs.map((p, i) => `<button class="mtile l" data-l="${i}">${UI.esc(p.l)}</button>`).join("")}</div>
        <div class="match-col">${rights.map((i) => `<button class="mtile r" data-r="${i}">${UI.esc(g.pairs[i].r)}</button>`).join("")}</div>
      </div>
      <div class="exp-fact" id="mhint">Tap a tile on the left, then its match on the right.</div>
    `));
    let selL = null; let done = 0;
    const hint = document.getElementById("mhint");
    const clearSel = () => document.querySelectorAll(".mtile.l.sel").forEach((x) => x.classList.remove("sel"));
    document.querySelectorAll(".mtile.l").forEach((b) => b.onclick = () => {
      if (b.classList.contains("matched")) return;
      clearSel(); b.classList.add("sel"); selL = b;
    });
    document.querySelectorAll(".mtile.r").forEach((b) => b.onclick = () => {
      if (!selL || b.classList.contains("matched")) return;
      M.engagement++;
      if (selL.dataset.l === b.dataset.r) {
        selL.classList.add("matched"); b.classList.add("matched"); selL.classList.remove("sel");
        selL = null; done++;
        if (done === g.pairs.length) { hint.textContent = "All matched! 🎉"; setTimeout(win, 500); }
      } else {
        b.classList.add("wrong"); const bad = b;
        setTimeout(() => bad.classList.remove("wrong"), 400);
        hint.textContent = "Not quite — try another match!";
      }
    });
  }

  function gameOrder(g, shell, win) {
    const correct = g.items;
    const shown = shuffle(correct.map((_, i) => i));
    UI.render(shell(`
      <div class="order-slots" id="slots">${correct.map((_, i) => `<span class="oslot" data-i="${i}">${i + 1}</span>`).join("")}</div>
      <div class="order-pool fadein">${shown.map((i) => `
        <button class="otile" data-i="${i}"><span>${correct[i].emoji}</span>${UI.esc(correct[i].label)}</button>`).join("")}</div>
      <div class="exp-fact" id="ohint">Tap them in the right order.</div>
    `));
    let expect = 0;
    const hint = document.getElementById("ohint");
    document.querySelectorAll(".otile").forEach((b) => b.onclick = () => {
      if (b.classList.contains("placed")) return;
      M.engagement++;
      if (+b.dataset.i === expect) {
        b.classList.add("placed");
        const slot = document.querySelector(`.oslot[data-i="${expect}"]`);
        slot.classList.add("filled"); slot.innerHTML = correct[expect].emoji;
        expect++;
        if (expect === correct.length) { hint.textContent = "Perfect order! 🎉"; setTimeout(win, 500); }
      } else {
        b.classList.add("shake"); const bad = b; setTimeout(() => bad.classList.remove("shake"), 400);
        hint.textContent = "Hmm, not next — try another!";
      }
    });
  }

  function gameChoose(g, shell, win) {
    UI.render(shell(`
      <div class="stack fadein" id="opts">
        ${g.options.map((o, i) => `<button class="choice" style="text-align:left" data-i="${i}">${UI.esc(o.t)}</button>`).join("")}
      </div>
      <div class="exp-fact" id="chint"></div>
    `));
    const hint = document.getElementById("chint");
    document.querySelectorAll("#opts .choice").forEach((b) => b.onclick = () => {
      const o = g.options[+b.dataset.i]; M.engagement++;
      hint.textContent = o.fx || "";
      if (o.ok) { b.classList.add("selected"); document.querySelectorAll("#opts .choice").forEach((x) => x.disabled = true); setTimeout(win, 700); }
      else { b.classList.add("nope"); const bad = b; setTimeout(() => bad.classList.remove("nope"), 500); }
    });
  }

  /* ---------- 3.3.4 QUIZ (adaptive + fail-safe) ---------- */
  function pQuiz(i, soloRevise) {
    const quiz = M.pb.quiz;
    if (i >= quiz.length) return soloRevise ? pReward() : pExplain();
    const q = quiz[i];
    const struggling = i > 0 && (M.quiz.correct / i) < 0.5;   // adaptive: show help if behind
    let wrongs = 0;
    UI.render(`
      ${header(soloRevise ? 3 : 3)}
      <div class="quiz-top"><span class="pill">🧠 Question ${i + 1}/${quiz.length}</span>
        ${M.mode === "challenge" ? `<span class="pill" style="color:var(--gold)">🔥 Challenge</span>` : ""}</div>
      <h2 class="title" style="font-size:21px;margin-top:14px">${UI.esc(q.q)}</h2>
      ${struggling ? `<div class="exp-fact">💡 ${UI.esc(q.hint)}</div>` : ""}
      <div class="stack" id="qopts" style="margin-top:8px">
        ${q.options.map((o, k) => `<button class="choice" style="text-align:left" data-k="${k}">${UI.esc(o)}</button>`).join("")}
      </div>
      <div class="exp-fact" id="qfb"></div>
    `);
    const fb = document.getElementById("qfb");
    const opts = [...document.querySelectorAll("#qopts .choice")];
    opts.forEach((b) => b.onclick = () => {
      const k = +b.dataset.k; M.quiz.attempts++;
      if (k === q.answer) {
        b.classList.add("correct");
        opts.forEach((x) => x.disabled = true);
        if (wrongs === 0) M.quiz.correct++;
        fb.innerHTML = `✅ ${UI.esc(q.explain)}`;
        setTimeout(() => pQuiz(i + 1, soloRevise), 1100);
      } else {
        wrongs++; b.classList.add("nope"); b.disabled = true;
        if (wrongs === 1) { fb.innerHTML = `💡 ${UI.esc(q.hint)}`; }
        else {  // fail-safe: reveal answer gently and move on
          opts.forEach((x) => x.disabled = true);
          opts[q.answer].classList.add("correct");
          fb.innerHTML = `🤝 No worries! ${UI.esc(q.explain)}`;
          setTimeout(() => pQuiz(i + 1, soloRevise), 1500);
        }
      }
    });
  }

  /* ---------- 3.3.5 AI EXPLANATION ---------- */
  function pExplain() {
    const e = M.pb.explanation;
    UI.render(`
      ${header(4)}
      <div class="mascot" style="background:var(--grad-cta)">🤖</div>
      <div class="bubble center" style="margin-bottom:14px">${UI.esc(e.analogy)}</div>
      <div class="memcard"><div class="mtitle">📌 Quick recap</div>
        <p class="muted" style="margin:8px 0 0;font-size:14px">${UI.esc(e.recap)}</p></div>
      <div class="cta-bar stack">
        <button class="btn btn--block" id="got">Got it! 🎁 Claim reward</button>
        <button class="btn btn--ghost btn--block" id="ask">🤖 Ask Wolio more</button>
      </div>
    `);
    document.getElementById("got").onclick = pReward;
    document.getElementById("ask").onclick = () => { if (window.Mentor) Mentor.open(); };
  }

  /* ---------- 3.3.6 + 3.3.7 REWARD + MEMORY SAVE ---------- */
  async function pReward() {
    const acc = M.quiz.total ? M.quiz.correct / M.quiz.total : 1;
    UI.render(`<div class="builder"><div class="ring"></div><p class="build-step">Saving to your brain… 🧬</p></div>`);
    let r;
    try {
      r = await API.missionFinish({
        user_id: App.userId(), world_id: M.world.id, mission_id: M.mission.id,
        accuracy: acc, time_ms: Date.now() - M.startTs, attempts: M.quiz.attempts,
        engagement: M.engagement, mode: M.mode,
      });
    } catch (e) { UI.toast("Saved offline — couldn't sync"); return Home.enter({}); }

    const stars = Math.max(1, Math.round(acc * 3));
    UI.render(`
      <div class="reward fadein">
        <div class="reward-burst">${M.mission.emoji}</div>
        <h1 class="title center" style="margin:0">Mission Complete!</h1>
        <div class="stars">${"⭐".repeat(stars)}${"▫️".repeat(3 - stars)}</div>
        <p class="subtitle center">${Math.round(acc * 100)}% accuracy · ${UI.esc(M.mission.concept)} locked in 🧠</p>
        <div class="tiles" style="margin:6px 0 4px">
          <div class="tile"><b>+${r.xp_earned}</b><span>XP</span></div>
          <div class="tile"><b>${r.mastery}%</b><span>mastery</span></div>
          <div class="tile"><b>${UI.esc(r.level)}</b><span>level</span></div>
        </div>
        ${r.leveled_up ? `<div class="pill" style="margin:8px auto 0;color:var(--gold)">⬆️ Level up: ${UI.esc(r.level)}!</div>` : ""}
      </div>
      <div class="cta-bar stack">
        <button class="btn btn--block" id="cont">Continue 🚀</button>
        <div class="row">
          <button class="btn btn--ghost" style="flex:1" id="again">🔁 Play again</button>
          <button class="btn btn--ghost" style="flex:1" id="chal">🔥 Challenge</button>
        </div>
      </div>
    `);
    document.getElementById("cont").onclick = () => Home.enter({});
    document.getElementById("again").onclick = () => replay(M.world.id, M.mission.id);
    document.getElementById("chal").onclick = () => challenge(M.world.id, M.mission.id);
  }

  /* ---------- quit ---------- */
  function _quit() {
    if (confirm("Leave this mission? Your progress this run won't be saved.")) Home.enter({});
  }

  function shuffle(a) { for (let i = a.length - 1; i > 0; i--) { const j = (i * 7 + 3) % (i + 1); [a[i], a[j]] = [a[j], a[i]]; } return a; }

  return { play, replay, challenge, revise, _quit };
})();
