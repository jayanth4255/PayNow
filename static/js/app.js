document.addEventListener("DOMContentLoaded", () => {
  const root = document.documentElement;
  const btn = document.getElementById("themeToggle");

  // Load saved theme or default to light
  const saved = localStorage.getItem("paynow-theme") || "light";
  root.setAttribute("data-theme", saved);

  // Update button icon if it exists
  if (btn) btn.textContent = saved === "dark" ? "☀️" : "🌙";

  // Toggle function
  const apply = mode => {
    root.setAttribute("data-theme", mode);
    localStorage.setItem("paynow-theme", mode);
    if (btn) btn.textContent = mode === "dark" ? "☀️" : "🌙";
  };

  if (btn) {
    btn.addEventListener("click", () => {
      const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      apply(next);
    });
  }
});

