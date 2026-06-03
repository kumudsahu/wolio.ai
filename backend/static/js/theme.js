/* Theme system — kids pick the look of their learning universe. */
window.Theme = (function () {
  const KEY = "wolio_theme";
  const THEMES = [
    { id: "cosmic", name: "Cosmic", emoji: "🌌" },
    { id: "comic",  name: "Comic",  emoji: "💥" },
    { id: "candy",  name: "Candy",  emoji: "🍭" },
    { id: "ocean",  name: "Ocean",  emoji: "🌊" },
    { id: "jungle", name: "Jungle", emoji: "🌿" },
    { id: "neon",   name: "Neon",   emoji: "🤖" },
  ];

  const DEFAULT = "comic";   // the app opens in the Comic look (kids can change it)
  function current() { return localStorage.getItem(KEY) || DEFAULT; }

  function apply(id, persist = true) {
    if (!THEMES.some((t) => t.id === id)) id = DEFAULT;
    document.body.setAttribute("data-theme", id);
    if (persist) localStorage.setItem(KEY, id);
    return id;
  }

  // Apply the saved theme immediately (before the app renders) to avoid a flash.
  apply(current(), false);

  return { THEMES, current, apply, list: () => THEMES };
})();
