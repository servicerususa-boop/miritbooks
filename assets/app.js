// Miritbooks.com — tiny enhancements. The site works fully without JavaScript.
(function () {
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Likes counter: counts up once to the target number on the 102 Likes page.
  document.querySelectorAll("[data-count-to]").forEach(function (el) {
    var target = parseInt(el.getAttribute("data-count-to"), 10);
    if (!target || reduce) { el.textContent = target || el.textContent; return; }
    var start = null, dur = 1700;
    function step(ts) {
      if (start === null) start = ts;
      var p = Math.min((ts - start) / dur, 1);
      el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3)));
      if (p < 1) requestAnimationFrame(step);
    }
    el.textContent = "0";
    requestAnimationFrame(step);
  });

  // Share buttons: native share sheet when available, otherwise copy the link.
  document.querySelectorAll("[data-share]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var url = btn.getAttribute("data-url") || location.href;
      var title = btn.getAttribute("data-title") || document.title;
      var status = document.querySelector("[data-share-status]");
      if (navigator.share) {
        navigator.share({ title: title, url: url }).catch(function () {});
      } else if (navigator.clipboard) {
        navigator.clipboard.writeText(url).then(function () {
          if (status) status.textContent = btn.getAttribute("data-done") || "Copied";
        });
      }
    });
  });
})();
