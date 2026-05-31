/* App bootstrap + lightweight session. */
window.App = (function () {
  const KEY = "wolio_user_id";
  const EMAIL_KEY = "wolio_email";
  let uid = null;

  function userId() { return uid; }
  function setUser(id) { uid = id; localStorage.setItem(KEY, String(id)); }
  function setEmail(e) { localStorage.setItem(EMAIL_KEY, e || ""); }
  function getEmail() { return localStorage.getItem(EMAIL_KEY) || ""; }
  function clear() { uid = null; localStorage.removeItem(KEY); localStorage.removeItem(EMAIL_KEY); }

  async function boot() {
    const saved = localStorage.getItem(KEY);
    if (saved) {
      try {
        const m = await API.me(saved);   // verify the user still exists
        if (m && m.theme) Theme.apply(m.theme);   // restore their chosen theme
        uid = Number(saved);
        return Home.enter({});
      } catch (_) { clear(); }
    }
    welcome();
  }

  function welcome() {
    UI.render(`
      <div class="center" style="margin:auto 0">
        <div class="mascot fadein" style="width:140px;height:140px;font-size:74px">🪐</div>
        <h1 class="title fadein delay-1" style="font-size:34px;margin-top:18px">wolio<span style="color:var(--cyan)">.ai</span></h1>
        <p class="subtitle fadein delay-1" style="font-size:17px">Your child doesn't study.<br>They <b>play, explore & become the hero</b> — and learning just happens.</p>
        <div class="row fadein delay-2" style="justify-content:center;gap:8px;flex-wrap:wrap;margin:8px 0 4px">
          <span class="pill">🎮 Play-to-learn</span><span class="pill">🤖 AI mentor</span><span class="pill">🧬 Never forget</span>
        </div>
      </div>
      <div class="cta-bar stack fadein delay-3">
        <button class="btn btn--block" id="start">Start my universe 🚀</button>
        <button class="btn btn--ghost btn--block" id="reset" style="display:${localStorage.getItem(KEY) ? "block" : "none"}">Reset demo</button>
      </div>
    `);
    document.getElementById("start").onclick = () => Auth.start();
    const reset = document.getElementById("reset");
    if (reset) reset.onclick = () => { clear(); UI.toast("Demo reset"); };
  }

  return { boot, welcome, userId, setUser, setUserId: setUser, setEmail, getEmail, clear };
})();

document.addEventListener("DOMContentLoaded", () => App.boot());
