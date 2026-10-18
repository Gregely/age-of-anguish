// Browser QA for the built index.html. Usage: node build/qa.cjs [path/to/index.html]
// Needs playwright (global install is fine: NODE_PATH=$(npm root -g)).
const path = require("path");
const { chromium } = require("playwright");

const file = path.resolve(process.argv[2] || path.join(__dirname, "..", "index.html"));
const url = "file://" + file;
const fails = [];
const ok = (cond, msg) => { if (!cond) fails.push(msg); else console.log("  ok  " + msg); };

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || undefined });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();
  const external = [];
  const errors = [];
  page.on("request", (r) => { if (!r.url().startsWith("file://") && !r.url().startsWith("data:")) external.push(r.url()); });
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  await page.goto(url);
  await page.waitForTimeout(300);

  ok(external.length === 0, "no external network requests" + (external.length ? ": " + external.slice(0, 3) : ""));
  ok((await page.locator("#view-map.on").count()) === 1, "landing view is the map");

  // every internal hash link resolves to a view (and anchor, if given)
  const broken = await page.evaluate(() => {
    const bad = [];
    const hrefs = new Set([...document.querySelectorAll('a[href^="#/"]')].map((a) => a.getAttribute("href")));
    hrefs.forEach((h) => {
      const p = h.replace(/^#\//, "").split("?")[0].split("/");
      if (!document.querySelector('.view[data-view="' + p[0] + '"]')) bad.push(h);
      else if (p[1] && !document.getElementById(p.slice(1).join("/"))) bad.push(h);
    });
    return { bad, n: hrefs.size };
  });
  ok(broken.bad.length === 0, `all ${broken.n} internal links resolve` + (broken.bad.length ? ": " + broken.bad.slice(0, 10).join(", ") : ""));

  const refs = await page.evaluate(() => {
    const bad = [];
    document.querySelectorAll("a.ref").forEach((a) => { const id = a.getAttribute("href").split("/").pop(); if (!document.getElementById(id)) bad.push(a.textContent); });
    return { bad, n: document.querySelectorAll("a.ref").length, broken: document.querySelectorAll(".broken").length };
  });
  ok(refs.bad.length === 0 && refs.broken === 0, `all ${refs.n} inline references resolve to sources; no broken markers`);

  // navigation to an entry opens and shows it
  const firstEntry = await page.evaluate(() => { const a = document.querySelector('.cards details.card'); return a && a.closest(".view").dataset.view + "/" + a.id; });
  if (firstEntry) {
    await page.goto(url + "#/" + firstEntry);
    await page.waitForTimeout(200);
    const open = await page.evaluate((id) => { const d = document.getElementById(id.split("/")[1]); return d.open && d.closest(".view").classList.contains("on"); }, firstEntry);
    ok(open, "deep link opens the target card in its view");
  }

  // search
  await page.goto(url + "#/map");
  const term = await page.evaluate(() => { const t = document.querySelector(".card-title"); return t ? t.textContent.split(/\s+/).find((w) => w.length > 4) : "the"; });
  await page.fill("#q", term);
  await page.waitForTimeout(500);
  const nres = await page.locator("#search-results li").count();
  ok(nres > 0, `search for "${term}" returns results (${nres})`);

  // filters
  await page.goto(url + "#/explore");
  await page.waitForTimeout(100);
  const total = await page.locator(".xrow:not([hidden])").count();
  const chip = page.locator('.fchip[data-key="strength"]:not(.zero)').first();
  await chip.click();
  const filtered = await page.locator(".xrow:not([hidden])").count();
  ok(filtered > 0 && filtered <= total, `strength filter narrows cards (${total} → ${filtered})`);
  await page.click("#fclear");
  ok((await page.locator(".xrow:not([hidden])").count()) === total, "clear filters restores all cards");
  await page.goto(url + "#/explore?strength=theory");
  await page.waitForTimeout(100);
  const preset = await page.locator('.fchip[data-val="theory"][aria-pressed="true"]').count();
  ok(preset === 1, "explore query-string preset applies a filter");

  // theme toggle
  const bg1 = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
  await page.click("#theme2"); await page.click("#theme2"); // auto -> light -> dark
  const bg2 = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
  ok(bg1 !== bg2, `theme toggle changes colours (${bg1} → ${bg2})`);

  // print emulation expands everything
  await page.goto(url + "#/" + (firstEntry ? firstEntry.split("/")[0] : "map"));
  await page.emulateMedia({ media: "print" });
  await page.evaluate(() => window.dispatchEvent(new Event("beforeprint")));
  const closed = await page.evaluate(() => [...document.querySelectorAll(".view.on details")].filter((d) => !d.open).length);
  ok(closed === 0, "print mode expands all collapsible sections");
  const sidebarHidden = await page.evaluate(() => getComputedStyle(document.getElementById("sidebar")).display === "none");
  ok(sidebarHidden, "print hides navigation");
  await page.emulateMedia({ media: "screen" });

  // mobile
  const m = await browser.newContext({ viewport: { width: 375, height: 780 }, isMobile: true });
  const mp = await m.newPage();
  mp.on("pageerror", (e) => errors.push(String(e)));
  const views = await page.evaluate(() => [...document.querySelectorAll(".view")].map((v) => v.dataset.view));
  const overflow = [];
  for (const v of views) {
    await mp.goto(url + "#/" + v);
    await mp.evaluate(() => document.querySelectorAll("details").forEach((d) => (d.open = true)));
    const w = await mp.evaluate(() => document.documentElement.scrollWidth);
    if (w > 376) overflow.push(v + ":" + w);
  }
  ok(overflow.length === 0, "no horizontal page overflow at 375px on any view" + (overflow.length ? ": " + overflow.join(", ") : ""));
  await mp.click("#navtoggle");
  ok(await mp.evaluate(() => document.body.classList.contains("nav-open")), "mobile nav drawer opens");

  ok(errors.length === 0, "no JS errors" + (errors.length ? ": " + errors.slice(0, 3).join(" | ") : ""));
  await browser.close();
  if (fails.length) { console.log("\nFAILED:\n - " + fails.join("\n - ")); process.exit(1); }
  console.log("\nAll QA checks passed.");
})();
