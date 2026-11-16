(() => {
  const root = document.documentElement;
  const key = "household-finance-theme";
  let saved;
  try { saved = localStorage.getItem(key); } catch {}
  let theme = saved === "dark" ? "dark" : "light";
  function apply() {
    root.dataset.theme = theme;
    const button = document.getElementById("theme-toggle");
    if (!button) return;
    const next = theme === "dark" ? "light" : "dark";
    button.textContent = next === "dark" ? "Dark" : "Light";
    button.setAttribute("aria-label", "Switch to " + next + " mode");
    button.setAttribute("aria-pressed", String(theme === "dark"));
    button.title = "Switch to " + next + " mode";
  }
  apply();
  document.addEventListener("DOMContentLoaded", () => {
    apply();
    document.getElementById("theme-toggle").addEventListener("click", () => {
      theme = theme === "dark" ? "light" : "dark";
      try { localStorage.setItem(key, theme); } catch {}
      apply();
    });
  });
})();
