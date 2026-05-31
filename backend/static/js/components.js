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
};
