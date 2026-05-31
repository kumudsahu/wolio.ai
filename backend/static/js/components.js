/* Tiny DOM helpers — no framework, just ergonomics. */
window.UI = {
  app: () => document.getElementById("app"),

  /** Replace the active screen with new HTML, animating it in. */
  render(html) {
    const app = UI.app();
    app.innerHTML = `<section class="screen">${html}</section>`;
    return app.querySelector(".screen");
  },

  /** Build an element from an HTML string. */
  h(html) {
    const t = document.createElement("template");
    t.innerHTML = html.trim();
    return t.content.firstElementChild;
  },

  toast(msg) {
    document.querySelectorAll(".toast").forEach((t) => t.remove());
    const t = UI.h(`<div class="toast">${msg}</div>`);
    document.querySelector(".stage").appendChild(t);
    requestAnimationFrame(() => t.classList.add("show"));
    setTimeout(() => {
      t.classList.remove("show");
      setTimeout(() => t.remove(), 300);
    }, 2200);
  },

  progressDots(step, total) {
    let dots = "";
    for (let i = 0; i < total; i++) dots += `<i class="${i <= step ? "active" : ""}"></i>`;
    return `<div class="progress-dots">${dots}</div>`;
  },

  esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  },

  /** Celebratory confetti burst (reward feedback, spec 5.10). */
  confetti(n = 80) {
    const stage = document.querySelector(".stage");
    if (!stage) return;
    const layer = UI.h(`<div class="confetti"></div>`);
    stage.appendChild(layer);
    const colors = ["#7c5cff", "#2ee6d6", "#ff6ba6", "#ffce4f", "#34e0a1"];
    for (let i = 0; i < n; i++) {
      const p = document.createElement("i");
      const left = Math.floor((i / n) * 100);
      const delay = (i % 10) * 40;
      const dur = 1400 + (i % 7) * 220;
      const rot = (i * 47) % 360;
      p.style.cssText =
        `left:${left}%;background:${colors[i % colors.length]};` +
        `animation-delay:${delay}ms;animation-duration:${dur}ms;transform:rotate(${rot}deg)`;
      layer.appendChild(p);
    }
    setTimeout(() => layer.remove(), 2600);
  },
};
