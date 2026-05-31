/* Email authentication — the first step after the welcome splash.
   Email → 6-digit code → either log in (returning) or start onboarding (new). */
window.Auth = (function () {
  let email = "";
  const DEV_CODE = "123456";   // dev master code — always works (see auth.py DEMO_AUTH_CODE)

  function start() { screenEmail(); }

  function screenEmail() {
    UI.render(`
      <div class="auth-head fadein">
        <div class="mascot">📧</div>
        <h1 class="title center">Let's set up your account</h1>
        <p class="subtitle center">Enter a parent's email — we'll send a quick code to keep things safe.</p>
      </div>
      <input class="field" id="email" type="email" inputmode="email" autocomplete="email"
             placeholder="you@email.com" value="${UI.esc(email)}" style="text-align:center" />
      <div id="err" class="auth-err"></div>
      <div class="cta-bar stack">
        <button class="btn btn--block" id="send">Send my code →</button>
        <button class="btn btn--ghost btn--block" id="back">← Back</button>
      </div>
    `);
    const input = document.getElementById("email");
    const err = document.getElementById("err");
    input.focus();
    const go = async () => {
      const e = input.value.trim().toLowerCase();
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(e)) { err.textContent = "Hmm, that doesn't look like an email."; return; }
      email = e; err.textContent = "";
      const btn = document.getElementById("send"); btn.disabled = true; btn.textContent = "Sending…";
      try {
        const r = await API.authSendCode(e);
        screenCode(r.demo_code);
      } catch (ex) {
        err.textContent = "Couldn't send the code. Try again."; btn.disabled = false; btn.textContent = "Send my code →";
      }
    };
    document.getElementById("send").onclick = go;
    input.addEventListener("keydown", (ev) => { if (ev.key === "Enter") go(); });
    document.getElementById("back").onclick = () => App.welcome();
  }

  function screenCode(demoCode) {
    UI.render(`
      <div class="auth-head fadein">
        <div class="mascot">📬</div>
        <h1 class="title center">Check your email</h1>
        <p class="subtitle center">We sent a 6-digit code to <b>${UI.esc(email)}</b></p>
      </div>
      <input class="field" id="code" inputmode="numeric" maxlength="6" autocomplete="one-time-code"
             value="${DEV_CODE}" placeholder="••••••" style="text-align:center;letter-spacing:8px;font-size:24px" />
      <div class="auth-demo">🔑 Dev code: <b>${DEV_CODE}</b> — always works${demoCode ? ` · sent: ${UI.esc(demoCode)}` : ""}</div>
      <div id="err" class="auth-err"></div>
      <div class="cta-bar stack">
        <button class="btn btn--block" id="verify">Verify & continue →</button>
        <button class="btn btn--ghost btn--block" id="change">Use a different email</button>
      </div>
    `);
    const input = document.getElementById("code");
    const err = document.getElementById("err");
    const btn = document.getElementById("verify");
    input.focus();
    input.addEventListener("input", () => {
      input.value = input.value.replace(/\D/g, "").slice(0, 6);
      btn.disabled = input.value.length < 4;
    });
    const go = async () => {
      const code = input.value.trim();
      if (code.length < 4) return;
      err.textContent = ""; btn.disabled = true; btn.textContent = "Verifying…";
      try {
        const r = await API.authVerify(email, code);
        App.setEmail(email);
        if (r.user_id) {                 // returning account → log straight in
          App.setUser(r.user_id);
          UI.toast("Welcome back! 👋");
          Home.enter({});
        } else {                         // new account → continue to onboarding
          Onboarding.start();
        }
      } catch (ex) {
        err.textContent = "That code isn't right. Try again."; btn.disabled = false; btn.textContent = "Verify & continue →";
      }
    };
    btn.onclick = go;
    input.addEventListener("keydown", (ev) => { if (ev.key === "Enter") go(); });
    document.getElementById("change").onclick = () => screenEmail();
  }

  return { start, screenEmail };
})();
