// Lightweight scroll-reveal: adds .in to .reveal elements as they enter view.
// Uses IntersectionObserver (never a scroll listener). Honors reduced motion by
// revealing everything immediately.
(function () {
  "use strict";
  const els = document.querySelectorAll(".reveal");
  if (!els.length) return;
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce || !("IntersectionObserver" in window)) {
    els.forEach((e) => e.classList.add("in"));
    return;
  }
  const io = new IntersectionObserver((entries) => {
    entries.forEach((en) => {
      if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); }
    });
  }, { threshold: 0.15, rootMargin: "0px 0px -8% 0px" });
  els.forEach((e) => io.observe(e));
})();

// Motivated micro-animation: flash the verdict only when the regime LABEL
// actually changes (a real state transition), not on every slider tick. Avoids
// strobing while still acknowledging when the classification flips.
(function () {
  "use strict";
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const name = document.getElementById("regime-name");
  if (!name) return;
  let prev = name.textContent.trim();
  const flash = (el) => { if (!el) return; el.classList.remove("flash"); void el.offsetWidth; el.classList.add("flash"); };
  const mo = new MutationObserver(() => {
    const cur = name.textContent.trim();
    if (cur && cur !== "—" && cur !== prev) { flash(name); prev = cur; }
  });
  mo.observe(name, { childList: true, characterData: true, subtree: true });
})();
