/* Floating AI Mentor — always-visible buddy with a chat sheet. */
window.Mentor = (function () {
  let history = [];

  function mount() {
    const root = document.getElementById("mentor-root");
    root.innerHTML = `<button class="fab" id="fab" title="Ask your mentor">🤖</button>`;
    document.getElementById("fab").onclick = open;
  }

  function open(seed) {
    const me = Home.getMe && Home.getMe();
    const name = me ? me.name : "buddy";
    const sheet = UI.h(`
      <div class="sheet">
        <div class="scrim"></div>
        <div class="panel">
          <div class="phead">
            <div class="mascot sm" style="width:42px;height:42px;font-size:22px;background:var(--grad-cta)">🤖</div>
            <div><b>Wolio</b><br><small>your AI buddy${me && me.tone ? " · " + me.tone : ""}</small></div>
            <button class="close">✕</button>
          </div>
          <div class="chat" id="chat"></div>
          <div class="chips" id="chips">
            <button class="chip" data-q="Explain gravity like I'm 8">🪐 Explain gravity</button>
            <button class="chip" data-q="Give me a fun fact">✨ Fun fact</button>
            <button class="chip" data-q="Quiz me on math">🧮 Quiz me</button>
          </div>
          <div class="composer">
            <input id="mi" placeholder="Ask me anything…" autocomplete="off" />
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
      addBot(chat, `Hey ${name}! 😎 I'm Wolio. Ask me anything — I'll explain it using stuff you love!`);
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
        const r = await API.mentor({ user_id: App.userId(), message: text,
          name: me2 && me2.name, interests: me2 && me2.interests,
          language: me2 && me2.language, tone: me2 && me2.tone, age_group: me2 && me2.age_group });
        typing.remove();
        addBot(chat, r.reply);
        history.push({ role: "bot", text: r.reply });
      } catch (e) {
        typing.remove();
        addBot(chat, "Oops, my brain hiccuped 😅 try again!");
      }
    };

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
