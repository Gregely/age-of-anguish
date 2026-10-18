(function () {
  "use strict";
  var DATA = JSON.parse(document.getElementById("site-data").textContent);
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var views = {};
  $$(".view").forEach(function (v) { views[v.dataset.view] = v; });

  function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } }

  /* ---------- theme ---------- */
  var themes = ["auto", "light", "dark"];
  function applyTheme(t) {
    if (t === "auto") document.documentElement.removeAttribute("data-theme");
    else document.documentElement.setAttribute("data-theme", t);
    var b2 = $("#theme2"); if (b2) b2.textContent = "Theme: " + t;
    var b = $("#theme"); if (b) b.setAttribute("aria-label", "Colour theme: " + t);
  }
  var theme = store("aoa-theme") || "auto";
  applyTheme(theme);
  function cycleTheme() { theme = themes[(themes.indexOf(theme) + 1) % 3]; store("aoa-theme", theme); applyTheme(theme); }
  $("#theme").addEventListener("click", cycleTheme);
  $("#theme2").addEventListener("click", cycleTheme);

  /* ---------- mobile drawer ---------- */
  var scrim = $("#scrim"), toggle = $("#navtoggle");
  function setNav(open) {
    document.body.classList.toggle("nav-open", open);
    scrim.hidden = !open;
    toggle.setAttribute("aria-expanded", String(open));
  }
  toggle.addEventListener("click", function () { setNav(!document.body.classList.contains("nav-open")); });
  scrim.addEventListener("click", function () { setNav(false); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") setNav(false); });

  /* ---------- backlinks ---------- */
  $$("[data-backlinks]").forEach(function (p) {
    var bl = DATA.backlinks[p.dataset.backlinks];
    if (!bl || !bl.length) return;
    p.innerHTML = "<b>Linked from:</b> " + bl.map(function (x) {
      return '<a href="' + x[0] + '">' + esc(x[1]) + "</a>";
    }).join(" · ");
  });
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  /* ---------- router ---------- */
  function parseHash() {
    var h = decodeURIComponent(location.hash.replace(/^#\/?/, ""));
    var q = "";
    var qi = h.indexOf("?");
    if (qi >= 0) { q = h.slice(qi + 1); h = h.slice(0, qi); }
    var parts = h.split("/");
    return { view: parts[0] || "map", anchor: parts.slice(1).join("/"), query: q };
  }
  function route() {
    var r = parseHash();
    var v = views[r.view];
    if (!v) {
      // bare element id fallback (e.g. old-style #src-3)
      var el = document.getElementById(r.view);
      var host = el && el.closest(".view");
      if (host) { r.anchor = r.view; r.view = host.dataset.view; v = host; } else { r.view = "map"; v = views.map; }
    }
    Object.keys(views).forEach(function (k) { views[k].classList.toggle("on", k === r.view); });
    $$(".side-nav a").forEach(function (a) {
      var target = a.getAttribute("href").replace(/^#\/?/, "").split(/[/?]/)[0];
      var on = target === r.view;
      a.classList.toggle("active", on);
      if (on) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current");
    });
    var title = $("h2", v);
    document.title = (title ? title.textContent + " · " : "") + "Age of Anguish";
    setNav(false);
    if (r.view === "explore") applyQuery(r.query);
    if (r.view === "search") { var q2 = $("#q2"); var p = new URLSearchParams(r.query); if (p.get("q") !== null) { q2.value = p.get("q"); runSearch(q2.value); } }
    if (r.anchor) {
      var t = document.getElementById(r.anchor);
      if (t) {
        var d = t.closest("details"); while (d) { d.open = true; d = d.parentElement && d.parentElement.closest("details"); }
        if (t.tagName === "DETAILS") t.open = true;
        requestAnimationFrame(function () {
          t.scrollIntoView({ block: "start" });
          t.classList.remove("flash"); void t.offsetWidth; t.classList.add("flash");
        });
        return;
      }
    }
    window.scrollTo(0, 0);
    $("#main").focus({ preventScroll: true });
  }
  window.addEventListener("hashchange", route);

  /* ---------- expand / collapse / print ---------- */
  document.addEventListener("click", function (e) {
    var b = e.target.closest("[data-act]");
    if (!b) return;
    var v = b.closest(".view");
    var act = b.dataset.act;
    if (act === "expand" || act === "collapse") $$("details", v).forEach(function (d) { d.open = act === "expand"; });
    if (act === "print") window.print();
  });
  var opened = [];
  window.addEventListener("beforeprint", function () {
    opened = $$("details:not([open])");
    opened.forEach(function (d) { d.open = true; });
  });
  window.addEventListener("afterprint", function () {
    opened.forEach(function (d) { d.open = false; });
    opened = [];
    document.body.classList.remove("print-all");
  });
  $("#printall").addEventListener("click", function () { document.body.classList.add("print-all"); window.print(); });

  /* ---------- map highlighting ---------- */
  var svg = $("svg.map");
  if (svg) {
    var edges = $$(".edge", svg);
    function hl(id) {
      if (!id) { svg.classList.remove("hl"); $$(".on", svg).forEach(function (n) { n.classList.remove("on"); }); return; }
      svg.classList.add("hl");
      var keep = {}; keep[id] = 1;
      edges.forEach(function (ed) {
        var on = ed.dataset.a === id || ed.dataset.b === id;
        ed.classList.toggle("on", on);
        if (on) { keep[ed.dataset.a] = 1; keep[ed.dataset.b] = 1; }
      });
      $$(".node", svg).forEach(function (n) { n.classList.toggle("on", !!keep[n.dataset.id]); });
    }
    $$(".node", svg).forEach(function (n) {
      n.addEventListener("mouseenter", function () { hl(n.dataset.id); });
      n.addEventListener("focus", function () { hl(n.dataset.id); });
      n.addEventListener("mouseleave", function () { hl(null); });
      n.addEventListener("blur", function () { hl(null); });
    });
  }

  /* ---------- explore filters ---------- */
  var rows = $$(".xrow");
  var chips = $$(".fchip");
  var active = {};
  function rowMatches(row, except) {
    for (var key in active) {
      if (key === except) continue;
      var vals = active[key];
      if (!vals.length) continue;
      var have = (row.dataset[key] || "").split("|");
      if (!vals.some(function (v) { return have.indexOf(v) >= 0; })) return false;
    }
    return true;
  }
  function refresh() {
    var n = 0;
    rows.forEach(function (r) { var m = rowMatches(r); r.hidden = !m; if (m) n++; });
    chips.forEach(function (c) {
      var key = c.dataset.key, val = c.dataset.val;
      var cnt = rows.filter(function (r) { return rowMatches(r, key) && (r.dataset[key] || "").split("|").indexOf(val) >= 0; }).length;
      $(".n", c).textContent = cnt;
      c.classList.toggle("zero", cnt === 0);
      c.setAttribute("aria-pressed", String((active[key] || []).indexOf(val) >= 0));
    });
    $("#fcount").textContent = n + " of " + rows.length + " cards shown";
  }
  chips.forEach(function (c) {
    c.addEventListener("click", function () {
      var k = c.dataset.key, v = c.dataset.val;
      active[k] = active[k] || [];
      var i = active[k].indexOf(v);
      if (i >= 0) active[k].splice(i, 1); else active[k].push(v);
      refresh();
    });
  });
  $("#fclear").addEventListener("click", function () { active = {}; refresh(); });
  function applyQuery(q) {
    if (!q) { refresh(); return; }
    active = {};
    new URLSearchParams(q).forEach(function (v, k) { (active[k] = active[k] || []).push(v); });
    refresh();
  }
  refresh();

  /* ---------- search ---------- */
  var docs = DATA.search.map(function (d) {
    return { d: d, t: norm(d.t), x: norm(d.x) };
  });
  function norm(s) { return String(s).toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, ""); }
  function runSearch(q) {
    var out = $("#search-results"), st = $("#search-status");
    var terms = norm(q).split(/[^a-z0-9'-]+/).filter(function (t) { return t.length > 1; });
    out.innerHTML = "";
    if (!terms.length) { st.textContent = "Type at least two letters."; return; }
    var res = [];
    docs.forEach(function (o) {
      var score = 0;
      for (var i = 0; i < terms.length; i++) {
        var t = terms[i];
        var inT = o.t.indexOf(t) >= 0, inX = o.x.indexOf(t) >= 0;
        if (!inT && !inX) return;
        score += (inT ? 10 : 0) + (inX ? 1 + Math.min(4, o.x.split(t).length - 1) : 0);
      }
      if (o.t.indexOf(terms.join(" ")) >= 0) score += 15;
      if (/^Card|^Thinker|^Tension|^Gap/.test(o.d.k)) score += 2;
      res.push([score, o]);
    });
    res.sort(function (a, b) { return b[0] - a[0]; });
    st.textContent = res.length + " result" + (res.length === 1 ? "" : "s") + " for “" + q + "”";
    var re = new RegExp("(" + terms.map(function (t) { return t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }).join("|") + ")", "gi");
    res.slice(0, 80).forEach(function (r) {
      var d = r[1].d, x = d.x, lx = r[1].x;
      var pos = lx.indexOf(terms[0]);
      var start = Math.max(0, pos - 80);
      var snip = (start > 0 ? "…" : "") + x.slice(start, start + 220) + (x.length > start + 220 ? "…" : "");
      var li = document.createElement("li");
      li.innerHTML = '<a href="' + d.u + '">' + esc(d.t).replace(re, "<mark>$1</mark>") + '</a><span class="k">' + esc(d.k) + '</span><span class="snip">' + esc(snip).replace(re, "<mark>$1</mark>") + "</span>";
      out.appendChild(li);
    });
  }
  var q = $("#q"), q2 = $("#q2"), timer;
  function goSearch(val) {
    if (parseHash().view !== "search") location.hash = "#/search";
    q2.value = val; runSearch(val);
  }
  q.addEventListener("input", function () { clearTimeout(timer); var v = q.value; timer = setTimeout(function () { if (v.trim()) goSearch(v); }, 180); });
  q.addEventListener("keydown", function (e) { if (e.key === "Enter") { e.preventDefault(); goSearch(q.value); q2.focus(); } });
  q2.addEventListener("input", function () { clearTimeout(timer); timer = setTimeout(function () { runSearch(q2.value); q.value = q2.value; }, 150); });
  document.addEventListener("keydown", function (e) {
    if (e.key === "/" && !/INPUT|TEXTAREA/.test(document.activeElement.tagName)) { e.preventDefault(); q.focus(); }
  });

  route();
})();
