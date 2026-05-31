/* Floating AI Mentor — always-visible buddy with a chat sheet. */
window.Mentor = (function () {
  let history = [];
  let mode = "fun";   // fun | quick | quiz

  /* The floating button is draggable — tap to open, drag to reposition.
     Stays inside the app frame and remembers where the kid put it. */
  function mount() {
    const root = document.getElementById("mentor-root");
    root.innerHTML = `<button class="fab" id="fab" title="Ask your mentor" aria-label="Ask your mentor">🤖</button>`;
    const fab = document.getElementById("fab");
    restorePos(fab);

    let startX = 0, startY = 0, offX = 0, offY = 0, dragging = false, moved = false;
    fab.addEventListener("pointerdown", (e) => {
      dragging = true; moved = false;
      const r = fab.getBoundingClientRect();
      startX = e.clientX; startY = e.clientY; offX = e.clientX - r.left; offY = e.clientY - r.top;
      try { fab.setPointerCapture(e.pointerId); } catch (_) {}
      fab.classList.add("dragging");
    });
    fab.addEventListener("pointermove", (e) => {
      if (!dragging) return;
      if (!moved && Math.hypot(e.clientX - startX, e.clientY - startY) > 6) moved = true;
      if (moved) { placeAt(fab, e.clientX - offX, e.clientY - offY); e.preventDefault(); }
    });
    const end = (e) => {
      if (!dragging) return;
      dragging = false; fab.classList.remove("dragging");
      try { fab.releasePointerCapture(e.pointerId); } catch (_) {}
      if (moved) savePos(fab); else open();   // tap (no drag) opens the chat
    };
    fab.addEventListener("pointerup", end);
    fab.addEventListener("pointercancel", end);
    window.addEventListener("resize", () => { const r = fab.getBoundingClientRect(); if (r.left || r.top) placeAt(fab, r.left, r.top); });
  }

  function appBox() {
    const a = document.querySelector(".app");
    return a ? a.getBoundingClientRect()
             : { left: 0, top: 0, right: innerWidth, bottom: innerHeight, width: innerWidth, height: innerHeight };
  }
  function placeAt(fab, x, y) {
    const b = appBox(), s = fab.offsetWidth || 60, pad = 10;
    x = Math.max(b.left + pad, Math.min(x, b.right - s - pad));
    y = Math.max(b.top + pad, Math.min(y, b.bottom - s - pad));
    fab.style.left = x + "px"; fab.style.top = y + "px"; fab.style.right = "auto"; fab.style.bottom = "auto";
  }
  function savePos(fab) {
    const b = appBox(), r = fab.getBoundingClientRect(), s = fab.offsetWidth || 60, pad = 10;
    const fx = (r.left - b.left - pad) / Math.max(1, b.width - s - 2 * pad);
    const fy = (r.top - b.top - pad) / Math.max(1, b.height - s - 2 * pad);
    const cl = (v) => Math.max(0, Math.min(1, v));
    try { localStorage.setItem("wolio_fab", JSON.stringify({ fx: cl(fx), fy: cl(fy) })); } catch (_) {}
  }
  function restorePos(fab) {
    let saved; try { saved = JSON.parse(localStorage.getItem("wolio_fab") || "null"); } catch (_) {}
    if (!saved) return;   // keep the CSS default (bottom-right) on first run
    const b = appBox(), s = 60, pad = 10;
    placeAt(fab, b.left + pad + saved.fx * (b.width - s - 2 * pad), b.top + pad + saved.fy * (b.height - s - 2 * pad));
  }

  function open(seed) {
    const me = Home.getMe && Home.getMe();
    const name = me ? me.name : "buddy";
    const topic = Home.getRecentTopic && Home.getRecentTopic();
    const sheet = UI.h(`
      <div class="sheet">
        <div class="scrim"></div>
        <div class="panel">
          <div class="phead">
            <div class="mascot sm" style="width:42px;height:42px;font-size:22px;background:var(--grad-cta)">🤖</div>
            <div><b>Wolio</b><br><small>your AI buddy${me && me.tone ? " · " + me.tone : ""}</small></div>
            <button class="close">✕</button>
          </div>
          <div class="modes" id="modes">
            <button class="mode-btn" data-mode="fun">😜 Fun</button>
            <button class="mode-btn" data-mode="quick">⚡ Quick</button>
            <button class="mode-btn" data-mode="quiz">🧠 Quiz</button>
          </div>
          <div class="chat" id="chat"></div>
          <div class="chips" id="chips">
            ${topic ? `<button class="chip" data-q="Explain ${UI.esc(topic)}">📌 Explain ${UI.esc(topic)}</button>` : ""}
            <button class="chip" data-q="Give me a fun fact">✨ Fun fact</button>
            <button class="chip" data-q="Quiz me">🧮 Quiz me</button>
          </div>
          <div class="composer">
            <input id="mi" placeholder="Ask about your learning universe…" autocomplete="off" />
            <button id="send">➤</button>
          </div>
        </div>
      </div>`);
    document.querySelector(".stage").appendChild(sheet);

    const chat = sheet.querySelector("#chat");
    const input = sheet.querySelector("#mi");
    const close = () => sheet.remove();
    sheet.querySelector(".scrim").onclick = close;
    sheet.querySelector(".close").onclick = close;

    if (!history.length) {
      addBot(chat, `Hey ${name}! 😎 I'm Wolio. Ask me about your learning universe 🌌 — space, math, stories, anything you're curious about!`);
    } else {
      history.forEach((m) => bubble(chat, m.role, m.text));
    }

    const send = async (text) => {
      text = (text || input.value).trim();
      if (!text) return;
      input.value = "";
      bubble(chat, "me", text);
      history.push({ role: "me", text });
      const typing = bubble(chat, "bot typing", "Wolio is thinking… 💭");
      try {
        const me2 = Home.getMe && Home.getMe();
        const r = await API.mentor({ user_id: App.userId(), message: text, mode,
          history: history.slice(-5), current_topic: Home.getRecentTopic && Home.getRecentTopic(),
          name: me2 && me2.name, interests: me2 && me2.interests,
          language: me2 && me2.language, tone: me2 && me2.tone, age_group: me2 && me2.age_group });
        typing.remove();
        addBot(chat, r.reply);
        history.push({ role: "bot", text: r.reply });
        // 9. healthy usage — gentle break reminder after a long session
        const turns = history.filter((m) => m.role === "me").length;
        if (turns > 0 && turns % 8 === 0) {
          setTimeout(() => addBot(chat, "You've explored a lot today 🚀 Maybe take a short adventure break and go play outside? I'll be here later! 🌳"), 900);
        }
      } catch (e) {
        typing.remove();
        addBot(chat, "Oops, my brain hiccuped 😅 try again!");
      }
    };

    // mode toggle (Fun / Quick / Quiz)
    const paintModes = () => sheet.querySelectorAll(".mode-btn").forEach((b) =>
      b.classList.toggle("active", b.dataset.mode === mode));
    sheet.querySelectorAll(".mode-btn").forEach((b) => b.onclick = () => { mode = b.dataset.mode; paintModes(); });
    paintModes();

    sheet.querySelector("#send").onclick = () => send();
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") send(); });
    sheet.querySelectorAll(".chip").forEach((c) => c.onclick = () => send(c.dataset.q));
    setTimeout(() => input.focus(), 200);
    if (seed) setTimeout(() => send(seed), 300);   // re-explain a memory card
  }

  function bubble(chat, cls, text) {
    const el = UI.h(`<div class="msg ${cls}">${UI.esc(text)}</div>`);
    chat.appendChild(el);
    chat.scrollTop = chat.scrollHeight;
    return el;
  }
  function addBot(chat, text) {
    const el = bubble(chat, "bot", "");
    let i = 0; // tiny typewriter for life
    (function type() {
      el.textContent = text.slice(0, i++);
      chat.scrollTop = chat.scrollHeight;
      if (i <= text.length) setTimeout(type, 12);
    })();
    return el;
  }

  return { mount, open };
})();
