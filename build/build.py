#!/usr/bin/env python3
"""Build the Age of Anguish atlas into one self-contained index.html.

Reads structured JSON from content/ (or --content DIR), renders every view to
static HTML, inlines CSS, JS, the search index and the map SVG, and fails
loudly on unknown source keys, broken cross-links or missing strength labels.

Inline markup used in content strings:
  **bold**, *italic*, [@key] or [@key1; @key2] citations,
  [[id]] or [[id|label]] cross-links to entries, thinkers, glossary terms,
  areas, tensions or gaps. Blank lines separate paragraphs.
"""
import argparse
import html
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent

STRENGTHS = {
    "WELL-SUPPORTED": ("well", "Empirically well-supported", "●",
                       "Replicated across designs or datasets, or backed by meta-analyses; the direction of effect is robust."),
    "CONTESTED": ("contested", "Supported but contested", "◐",
                  "Real evidence exists but is mixed, small-effect, confounded or credibly disputed."),
    "THEORETICAL": ("theory", "Theoretical / interpretive", "◇",
                    "A coherent framework judged on explanatory power; not tested or not straightforwardly testable."),
    "SPECULATIVE": ("spec", "Speculative", "○",
                    "Plausible, but with thin or no supporting evidence."),
    "CONTRADICTED": ("contra", "Contradicted by evidence", "✕",
                     "The best available evidence points against it."),
}

THEMES = {
    "community-belonging": "Community & belonging",
    "work-economy": "Work & economy",
    "meaning-purpose": "Meaning & purpose",
    "self-identity": "Self & identity",
    "status-comparison": "Status & comparison",
    "time-acceleration": "Time & acceleration",
    "technology-attention": "Technology & attention",
    "body-biology": "Body & biology",
    "measurement-diagnosis": "Measurement & diagnosis",
    "stigma-silence": "Stigma & silence",
    "future-ecology": "Future & ecology",
    "institutions-power": "Institutions & power",
    "ritual-religion": "Ritual & religion",
    "treatment-help": "Treatment & help",
}

LAYERS = [
    ("time", "Time, future & ecology"),
    ("culture", "Culture & meaning"),
    ("technology", "Technology & attention"),
    ("institutions", "Institutions & economy"),
    ("relationships", "Relationships & community"),
    ("mind", "The individual mind"),
    ("body", "Body & brain"),
    ("premise", "The premise: is it rising?"),
]
LAYER_NAMES = dict(LAYERS)

EDGE_TYPES = {
    "reinforces": "reinforces / overlaps with",
    "mechanism": "proposed mechanism for",
    "tension": "in tension with",
}


class BuildError(Exception):
    pass


def esc(s):
    return html.escape(str(s), quote=True)


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


class Site:
    def __init__(self, cdir):
        self.cdir = Path(cdir)
        self.errors = []
        self.warnings = []
        load = lambda n, d=None: self._load(n, d)
        self.meta = load("meta.json", {})
        self.areas = load("areas.json", [])
        self.entries = load("entries.json", [])
        self.thinkers = load("thinkers.json", [])
        self.sources = load("sources.json", {})
        self.glossary = load("glossary.json", [])
        self.reading = load("reading.json", [])
        self.tensions = load("tensions.json", [])
        self.gaps = load("gaps.json", [])
        self.helps = load("helps.json", {})
        self.mapdata = load("map.json", {"nodes": [], "edges": []})
        self.method = load("method.json", {})
        self.area_by_id = {a["id"]: a for a in self.areas}
        self.entry_by_id = {}
        for e in self.entries:
            if e["id"] in self.entry_by_id:
                self.errors.append(f"duplicate entry id {e['id']}")
            self.entry_by_id[e["id"]] = e
        self.backrefs = {}  # source key -> {(href, label)}
        self.ctx = None     # (href, label) of the thing currently being rendered
        self._number_sources()
        self._build_anchor_registry()
        self.cross_backlinks = {}  # entry id -> set of (href,label) linking to it

    def _load(self, name, default):
        p = self.cdir / name
        if not p.exists():
            if default is None:
                raise BuildError(f"missing {p}")
            self.warnings.append(f"{name} not found; using empty default")
            return default
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as ex:
            raise BuildError(f"{name}: {ex}")

    # ---------- registries ----------
    def _number_sources(self):
        def sort_key(k):
            return re.sub(r"[^a-z0-9 ]", "", self.sources[k]["cite"].lower())
        self.src_order = sorted(self.sources, key=sort_key)
        self.src_num = {k: i + 1 for i, k in enumerate(self.src_order)}

    def _build_anchor_registry(self):
        reg = {}

        def add(i, href, label, kind):
            if i in reg:
                self.errors.append(f"anchor id collision: {i} ({reg[i][2]} vs {kind})")
            reg[i] = (href, label, kind)
        for a in self.areas:
            add(a["id"], f"#/{a['id']}", a["title"], "area")
        for e in self.entries:
            add(e["id"], f"#/{e['area']}/e-{e['id']}", e["title"], "entry")
        for t in self.thinkers:
            add(t["id"], f"#/thinkers/t-{t['id']}", t["name"], "thinker")
        for g in self.glossary:
            gid = g.get("id") or "g-" + slug(g["term"])
            g["id"] = gid
            add(gid, f"#/glossary/{gid}", g["term"], "glossary")
        for t in self.tensions:
            add(t["id"], f"#/tensions/{t['id']}", t["title"], "tension")
        for g in self.gaps:
            add(g["id"], f"#/gaps/{g['id']}", g["title"], "gap")
        self.anchors = reg

    def link(self, i, label=None, cls="xref"):
        if i not in self.anchors:
            self.errors.append(f"broken cross-link [[{i}]] in {self.ctx[1] if self.ctx else '?'}")
            return f'<span class="xref broken">{esc(label or i)}</span>'
        href, lab, kind = self.anchors[i]
        if kind == "entry" and self.ctx:
            self.cross_backlinks.setdefault(i, set()).add(self.ctx)
        return f'<a class="{cls} k-{kind}" href="{href}">{esc(label or lab)}</a>'

    # ---------- inline markup ----------
    CITE_RE = re.compile(r"\[(@[^\]]+)\]")
    XREF_RE = re.compile(r"\[\[([a-z0-9:_\-]+)(?:\|([^\]]+))?\]\]")

    def cite(self, keys):
        out = []
        keys = sorted({k.strip().lstrip("@").strip() for k in keys}, key=lambda k: self.src_num.get(k, 0))
        for k in keys:
            if not k:
                continue
            if k not in self.src_num:
                self.errors.append(f"unknown source key @{k} in {self.ctx[1] if self.ctx else '?'}")
                out.append(f'<span class="ref broken">?{esc(k)}</span>')
                continue
            n = self.src_num[k]
            if self.ctx:
                self.backrefs.setdefault(k, set()).add(self.ctx)
            out.append(f'<a class="ref" href="#/sources/src-{n}" title="{esc(self.sources[k]["cite"][:160])}">{n}</a>')
        return '<sup class="cites">[' + ", ".join(out) + "]</sup>"

    def inline(self, s):
        if s is None:
            return ""
        s = str(s)
        placeholders = []

        def stash(h):
            placeholders.append(h)
            return f"\x00{len(placeholders) - 1}\x00"
        s = self.CITE_RE.sub(lambda m: stash(self.cite(m.group(1).split(";"))), s)
        s = self.XREF_RE.sub(lambda m: stash(self.link(m.group(1), m.group(2))), s)
        s = esc(s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
        s = re.sub(r"\x00(\d+)\x00", lambda m: placeholders[int(m.group(1))], s)
        return s

    def para(self, s):
        if not s:
            return ""
        if isinstance(s, list):
            s = "\n\n".join(s)
        blocks = [b.strip() for b in re.split(r"\n\s*\n", str(s)) if b.strip()]
        out = []
        for b in blocks:
            lines = b.split("\n")
            if all(l.lstrip().startswith(("- ", "* ")) for l in lines):
                out.append("<ul>" + "".join(f"<li>{self.inline(l.lstrip()[2:])}</li>" for l in lines) + "</ul>")
            else:
                out.append(f"<p>{self.inline(' '.join(lines))}</p>")
        return "\n".join(out)

    def bullets(self, items):
        if not items:
            return ""
        return "<ul>" + "".join(f"<li>{self.inline(x)}</li>" for x in items) + "</ul>"

    # ---------- components ----------
    def badge(self, strength, note=None, small=False):
        if strength not in STRENGTHS:
            raise BuildError(f"bad strength {strength!r}")
        cls, label, icon, _ = STRENGTHS[strength]
        t = f' title="{esc(note)}"' if note else ""
        return (f'<span class="badge s-{cls}{" sm" if small else ""}"{t}>'
                f'<span class="ic" aria-hidden="true">{icon}</span>{esc(label)}</span>')

    def chips(self, items, kind):
        return "".join(f'<span class="chip c-{kind}">{esc(x)}</span>' for x in items)

    def entry_card(self, e):
        href = f"#/{e['area']}/e-{e['id']}"
        self.ctx = (href, e["title"])
        if e.get("strength") not in STRENGTHS:
            self.errors.append(f"entry {e['id']} missing/invalid strength")
            e["strength"] = "SPECULATIVE"
        if not e.get("strength_note"):
            self.errors.append(f"entry {e['id']} missing strength_note")
        for th in e.get("themes", []):
            if th not in THEMES:
                self.errors.append(f"entry {e['id']} unknown theme {th}")
        if e.get("layer") not in LAYER_NAMES:
            self.errors.append(f"entry {e['id']} bad layer {e.get('layer')}")
        parts = []
        parts.append(f'<div class="claim"><h4>Core claim</h4>{self.para(e["claim"])}</div>')
        if e.get("proponents"):
            parts.append(f'<p class="meta-line"><b>Proponents:</b> {self.inline(", ".join(e["proponents"]))}</p>')
        parts.append('<div class="evid">')
        parts.append(f'<div class="ev ev-for"><h4>Evidence &amp; arguments for</h4>{self.bullets(e.get("for", []))}</div>')
        parts.append(f'<div class="ev ev-against"><h4>Evidence &amp; arguments against</h4>{self.bullets(e.get("against", []))}</div>')
        parts.append("</div>")
        parts.append(f'<div class="strength-box">{self.badge(e["strength"])} <span>{self.inline(e.get("strength_note", ""))}</span></div>')
        if e.get("critics"):
            parts.append(f'<p class="meta-line"><b>Key critics:</b> {self.inline("; ".join(e["critics"]))}</p>')
        if e.get("quote"):
            q = e["quote"]
            parts.append(f'<blockquote>“{esc(q["text"])}” <cite>{self.inline(q.get("by", ""))}</cite></blockquote>')
        if e.get("sources"):
            parts.append(f'<p class="meta-line"><b>Key sources:</b> {self.cite(e["sources"])}</p>')
        rel = e.get("related", [])
        if rel:
            links = [self.link(r) for r in rel]
            parts.append(f'<p class="meta-line related"><b>Related:</b> {" · ".join(links)}</p>')
        parts.append(f'<p class="backlinks" data-backlinks="{esc(e["id"])}"></p>')
        disc = e.get("disciplines", [])
        themes = [THEMES.get(t, t) for t in e.get("themes", [])]
        data = (f'data-strength="{STRENGTHS[e["strength"]][0]}" data-disc="{esc("|".join(disc))}" '
                f'data-themes="{esc("|".join(e.get("themes", [])))}" data-area="{esc(e["area"])}"')
        head = (f'<summary><span class="card-title">{esc(e["title"])}</span>'
                f'<span class="card-badges">{self.badge(e["strength"], e.get("strength_note"), small=True)}'
                f'<span class="type">{esc(e.get("type", ""))}</span></span>'
                f'<span class="card-tags">{self.chips(disc, "disc")}{self.chips(themes, "theme")}</span></summary>')
        self.ctx = None
        return (f'<details class="card" id="e-{esc(e["id"])}" {data}>{head}'
                f'<div class="card-body">{"".join(parts)}</div></details>')

    def section(self, vid, title, body, kicker=None, tools=True):
        k = f'<p class="kicker">{esc(kicker)}</p>' if kicker else ""
        t = ('<div class="view-tools"><button type="button" data-act="expand">Expand all</button>'
             '<button type="button" data-act="collapse">Collapse all</button>'
             '<button type="button" data-act="print">Print this section</button></div>') if tools else ""
        return (f'<section class="view" id="view-{vid}" data-view="{vid}" aria-labelledby="h-{vid}">'
                f'<header class="view-head">{k}<h2 id="h-{vid}">{esc(title)}</h2>{t}</header>{body}</section>')

    def subsection(self, sid, title, body, open_=False):
        return (f'<details class="sub" id="{esc(sid)}"{" open" if open_ else ""}>'
                f'<summary><h3>{esc(title)}</h3></summary><div class="sub-body">{body}</div></details>')

    # ---------- views ----------
    def view_area(self, a):
        self.ctx = (f"#/{a['id']}", a["title"])
        body = [f'<div class="overview">{self.para(a.get("overview"))}</div>']
        ents = [e for e in self.entries if e["area"] == a["id"]]
        if not ents:
            self.warnings.append(f"area {a['id']} has no entries")
        counts = {}
        for e in ents:
            counts[e["strength"]] = counts.get(e["strength"], 0) + 1
        dist = " ".join(f'{self.badge(s, small=True)}<span class="cnt">×{counts[s]}</span>'
                        for s in STRENGTHS if s in counts)
        body.append(f'<p class="dist"><b>{len(ents)} {"entry" if len(ents) == 1 else "entries"}.</b> {dist}</p>')
        body.append('<div class="cards">' + "".join(self.entry_card(e) for e in ents) + "</div>")
        self.ctx = (f"#/{a['id']}", a["title"])
        for key, title in (("steelman", "Steelman of the rival / deflationary view"),
                           ("internal_tensions", "Tensions within this area"),
                           ("cross_tensions", "Tensions with other areas"),
                           ("open_questions", "Open questions: what this area cannot explain")):
            if a.get(key):
                body.append(self.subsection(f"{a['id']}-{key}", title, self.para(a[key])))
        self.ctx = None
        return self.section(a["id"], a["title"], "\n".join(body), kicker=a.get("kicker"))

    def view_map(self):
        m = self.meta
        intro = self.para(m.get("intro", ""))
        legend = "".join(
            f'<li><a href="#/explore?strength={c}">{self.badge(k)}</a> <span>{esc(d)}</span></li>'
            for k, (c, _l, _i, d) in STRENGTHS.items())
        edge_legend = "".join(f'<li><svg width="34" height="10" aria-hidden="true"><line x1="0" y1="5" x2="34" y2="5" class="edge e-{k}"/></svg> {esc(v)}</li>'
                              for k, v in EDGE_TYPES.items())
        layer_list = []
        for lid, lname in LAYERS:
            items = [e for e in self.entries if e.get("layer") == lid]
            areas = sorted({self.area_by_id[e["area"]]["short"] for e in items if e["area"] in self.area_by_id})
            links = ", ".join(self.link(e["id"]) for e in items[:12])
            more = f' <a href="#/explore?layer={lid}">and {len(items) - 12} more</a>' if len(items) > 12 else ""
            layer_list.append(f'<li><b>{esc(lname)}</b> <span class="muted">({len(items)} entries; areas: {esc(", ".join(areas))})</span><br>{links}{more}</li>')
        areas_grid = "".join(
            f'<a class="area-tile" href="#/{a["id"]}"><span class="num">{esc(a.get("num", ""))}</span>'
            f'<b>{esc(a["title"])}</b><span>{esc(a.get("blurb", ""))}</span></a>' for a in self.areas)
        body = f"""
<div class="intro">{intro}</div>
<div class="notice">{self.para(m.get("no_thesis", ""))}</div>
<h3 class="h3">The territory, as a diagram</h3>
<p class="muted">{esc(m.get("map_caption", ""))}</p>
<div class="map-wrap" role="group" aria-label="Diagram of theories by layer of explanation">{self.map_svg()}</div>
<div class="legends"><div><h4>Evidence labels</h4><ul class="legend">{legend}</ul></div>
<div><h4>Connections</h4><ul class="legend">{edge_legend}</ul><p class="muted small">Hover or focus a node to highlight its connections; click to open its card.</p></div></div>
<h3 class="h3">The layers, in text</h3>
<ol class="layers-text">{"".join(layer_list)}</ol>
<h3 class="h3">Research areas</h3>
<div class="area-grid">{areas_grid}</div>
<h3 class="h3">How to use this atlas</h3>
{self.para(m.get("howto", ""))}
"""
        return self.section("map", m.get("title", "Map of the territory"), body, kicker="Start here", tools=False)

    def map_svg(self):
        nodes = self.mapdata.get("nodes", [])
        edges = self.mapdata.get("edges", [])
        W, band, padl = 1180, 112, 190
        H = band * len(LAYERS) + 20
        pos = {}
        by_layer = {l: [] for l, _ in LAYERS}
        for n in nodes:
            e = self.entry_by_id.get(n)
            if not e:
                self.errors.append(f"map node {n} is not an entry")
                continue
            by_layer[e["layer"]].append(e)
        out = [f'<svg class="map" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="map-title map-desc">',
               '<title id="map-title">Layers of explanation</title>',
               '<desc id="map-desc">Each band is a layer of explanation; each node is a theory or finding, shaped by evidence strength. Lines show reinforcing, mechanistic or conflicting relations.</desc>']
        for i, (lid, lname) in enumerate(LAYERS):
            y = 10 + i * band
            out.append(f'<rect class="band b{i % 2}" x="0" y="{y}" width="{W}" height="{band}" rx="6"/>')
            out.append(f'<text class="band-label" x="14" y="{y + band / 2 + 5}">{esc(lname)}</text>')
            items = by_layer[lid]
            k = len(items)
            if not k:
                continue
            rows = 2 if k > 6 else 1
            per = math.ceil(k / rows)
            for j, e in enumerate(items):
                r, c = divmod(j, per)
                cnt = per if r < rows - 1 else k - per * (rows - 1)
                span = W - padl - 30
                x = padl + span * (c + 0.5) / cnt + (r % 2) * (span / cnt / 4 if rows > 1 else 0)
                yy = y + band * ((r + 1) / (rows + 1)) if rows > 1 else y + band / 2
                pos[e["id"]] = (x, yy)
        out.append('<g class="edges">')
        for ed in edges:
            a, b, t = ed["from"], ed["to"], ed.get("type", "reinforces")
            if a not in pos or b not in pos:
                self.errors.append(f"map edge {a}->{b} references missing node")
                continue
            if t not in EDGE_TYPES:
                self.errors.append(f"map edge {a}->{b} bad type {t}")
            (x1, y1), (x2, y2) = pos[a], pos[b]
            mx = (x1 + x2) / 2 + (y2 - y1) * 0.15
            my = (y1 + y2) / 2 - (x2 - x1) * 0.08
            note = esc(ed.get("note", ""))
            out.append(f'<path class="edge e-{t}" data-a="{a}" data-b="{b}" d="M{x1:.0f},{y1:.0f} Q{mx:.0f},{my:.0f} {x2:.0f},{y2:.0f}"><title>{esc(self.entry_by_id[a]["title"])} — {esc(EDGE_TYPES.get(t, t))} — {esc(self.entry_by_id[b]["title"])}{": " + note if note else ""}</title></path>')
        out.append("</g><g class=\"nodes\">")
        for nid, (x, y) in pos.items():
            e = self.entry_by_id[nid]
            cls = STRENGTHS[e["strength"]][0]
            label = e.get("short") or e["title"]
            lines = wrap(label, 18)
            tw = max(len(l) for l in lines) * 6.6 + 18
            th = 15 * len(lines) + 10
            texts = "".join(f'<tspan x="{x:.0f}" dy="{0 if i == 0 else 15}">{esc(l)}</tspan>' for i, l in enumerate(lines))
            out.append(
                f'<a href="#/{e["area"]}/e-{nid}" class="node s-{cls}" data-id="{nid}" tabindex="0">'
                f'<title>{esc(e["title"])} ({esc(STRENGTHS[e["strength"]][1])})</title>'
                f'<rect x="{x - tw / 2:.0f}" y="{y - th / 2:.0f}" width="{tw:.0f}" height="{th:.0f}" rx="{8 if cls != "theory" else 2}"/>'
                f'<text x="{x:.0f}" y="{y - th / 2 + 17:.0f}">{texts}</text></a>')
        out.append("</g></svg>")
        return "".join(out)

    def view_explore(self):
        discs = sorted({d for e in self.entries for d in e.get("disciplines", [])})
        def group(name, key, opts):
            btns = "".join(f'<button type="button" class="fchip" data-key="{key}" data-val="{esc(v)}" aria-pressed="false">{lab}<span class="n"></span></button>'
                           for v, lab in opts)
            return f'<fieldset class="fgroup"><legend>{esc(name)}</legend>{btns}</fieldset>'
        strength_opts = [(c, f'<span aria-hidden="true">{i}</span> {esc(l)}') for _k, (c, l, i, _d) in STRENGTHS.items()]
        theme_opts = [(k, esc(v)) for k, v in THEMES.items()]
        area_opts = [(a["id"], esc(a["short"])) for a in self.areas]
        layer_opts = [(l, esc(n)) for l, n in LAYERS]
        disc_opts = [(d, esc(d)) for d in discs]
        rows = []
        for e in self.entries:
            self.ctx = None
            a = self.area_by_id.get(e["area"], {"short": e["area"]})
            claim = re.sub(r"<[^>]+>", "", self.inline(e["claim"] if isinstance(e["claim"], str) else " ".join(e["claim"])))
            claim = claim[:260] + ("…" if len(claim) > 260 else "")
            rows.append(
                f'<li class="xrow" data-strength="{STRENGTHS[e["strength"]][0]}" data-disc="{esc("|".join(e.get("disciplines", [])))}" '
                f'data-themes="{esc("|".join(e.get("themes", [])))}" data-area="{esc(e["area"])}" data-layer="{esc(e.get("layer", ""))}">'
                f'<a href="#/{e["area"]}/e-{e["id"]}"><b>{esc(e["title"])}</b></a> {self.badge(e["strength"], small=True)}'
                f' <span class="muted small">{esc(a["short"])} · {esc(LAYER_NAMES.get(e.get("layer"), ""))}</span><br><span class="small">{claim}</span></li>')
        body = f"""
<p>Filter every card in the atlas. Options within a group are combined with OR; groups are combined with AND. Numbers show how many cards each option would match given the other active filters.</p>
<div class="filters">
{group("Evidence strength", "strength", strength_opts)}
{group("Theme", "themes", theme_opts)}
{group("Discipline", "disc", disc_opts)}
{group("Research area", "area", area_opts)}
{group("Layer", "layer", layer_opts)}
<p><button type="button" id="fclear">Clear all filters</button> <span id="fcount" aria-live="polite"></span></p>
</div>
<ul class="xlist">{"".join(rows)}</ul>"""
        return self.section("explore", "Explore & filter all cards", body, kicker="Reference", tools=False)

    def view_tensions(self):
        out = [self.para(self.meta.get("tensions_intro", ""))]
        for t in self.tensions:
            self.ctx = (f"#/tensions/{t['id']}", t["title"])
            sides = "".join(
                f'<div class="side"><h4>{esc(s["label"])}</h4>{self.para(s["claim"])}'
                + (f'<p class="meta-line"><b>See:</b> {" · ".join(self.link(x) for x in s.get("entries", []))}</p>' if s.get("entries") else "")
                + "</div>" for s in t["sides"])
            crux = f'<div class="crux"><h4>Where the disagreement turns</h4>{self.para(t.get("crux"))}</div>' if t.get("crux") else ""
            ev = f'<div class="crux"><h4>What evidence could decide it</h4>{self.para(t.get("evidence"))}</div>' if t.get("evidence") else ""
            out.append(self.subsection(t["id"], t["title"], f'{self.para(t.get("summary"))}<div class="sides">{sides}</div>{crux}{ev}'))
        self.ctx = None
        return self.section("tensions", "Tensions & contradictions between frameworks", "\n".join(out), kicker="Across the frameworks")

    def view_gaps(self):
        out = [self.para(self.meta.get("gaps_intro", ""))]
        for g in self.gaps:
            self.ctx = (f"#/gaps/{g['id']}", g["title"])
            see = f'<p class="meta-line"><b>Frameworks that come closest:</b> {" · ".join(self.link(x) for x in g.get("entries", []))}</p>' if g.get("entries") else ""
            out.append(self.subsection(g["id"], g["title"], self.para(g["text"]) + see))
        self.ctx = None
        return self.section("gaps", "Gaps: what no framework explains well", "\n".join(out), kicker="Across the frameworks")

    def view_helps(self):
        h = self.helps
        self.ctx = ("#/helps", "What helps")
        out = [self.para(h.get("intro", ""))]
        if h.get("table"):
            rows = "".join(
                f'<tr><th scope="row">{self.inline(r["what"])}</th><td>{self.badge(r["strength"], small=True)}</td><td>{self.inline(r["finding"])}</td><td>{self.inline(r.get("caveats", ""))}</td></tr>'
                for r in h["table"])
            out.append(f'<div class="table-wrap"><table class="helps"><thead><tr><th scope="col">Intervention</th><th scope="col">Evidence</th><th scope="col">What the best evidence shows</th><th scope="col">Caveats</th></tr></thead><tbody>{rows}</tbody></table></div>')
        ints = [e for e in self.entries if e.get("type") == "intervention"]
        if ints:
            out.append('<h3 class="h3">Intervention cards</h3><ul class="plain">' + "".join(
                f'<li>{self.link(e["id"])} {self.badge(e["strength"], small=True)}</li>' for e in ints) + "</ul>")
        out.append(self.para(h.get("outro", "")))
        self.ctx = None
        return self.section("helps", "What helps: the evidence", "\n".join(out), kicker="Across the frameworks")

    def view_thinkers(self):
        ts = sorted(self.thinkers, key=lambda t: t.get("sort", t["name"].split()[-1]).lower())
        letters = sorted({t.get("sort", t["name"].split()[-1])[0].upper() for t in ts})
        nav = " ".join(f'<a href="#/thinkers/L-{l}">{l}</a>' for l in letters)
        out = [f'<p>{len(ts)} thinkers, researchers and writers, alphabetical by surname. Each lists key ideas, key works and key critics.</p><p class="alpha">{nav}</p>']
        cur = None
        for t in ts:
            first = t.get("sort", t["name"].split()[-1])[0].upper()
            if first != cur:
                cur = first
                out.append(f'<h3 class="letter" id="L-{cur}">{cur}</h3>')
            self.ctx = (f"#/thinkers/t-{t['id']}", t["name"])
            areas = " · ".join(self.link(a) for a in t.get("areas", []))
            ents = " · ".join(self.link(x) for x in t.get("entries", []))
            body = (f'<p class="meta-line"><b>Field:</b> {esc(t.get("field", ""))}{" · <b>Areas:</b> " + areas if areas else ""}</p>'
                    f'<h4>Key ideas</h4>{self.para(t.get("ideas"))}'
                    + (f'<h4>Key works</h4>{self.bullets(t.get("works", []))}' if t.get("works") else "")
                    + (f'<h4>Key critics &amp; critiques</h4>{self.para(t.get("critics"))}' if t.get("critics") else "")
                    + (f'<p class="meta-line"><b>Cards:</b> {ents}</p>' if ents else ""))
            dates = f' <span class="dates">({esc(t["dates"])})</span>' if t.get("dates") else ""
            out.append(f'<details class="card person" id="t-{esc(t["id"])}"><summary><span class="card-title">{esc(t["name"])}{dates}</span>'
                       f'<span class="card-tags"><span class="chip c-disc">{esc(t.get("field", ""))}</span></span></summary><div class="card-body">{body}</div></details>')
        self.ctx = None
        return self.section("thinkers", "Who's who", "\n".join(out), kicker="Reference")

    def view_glossary(self):
        gs = sorted(self.glossary, key=lambda g: g["term"].lower().lstrip("'\"‘“"))
        out = [f"<p>{len(gs)} terms as they are used in the literatures covered here.</p><dl class=\"gloss\">"]
        for g in gs:
            self.ctx = (f"#/glossary/{g['id']}", g["term"])
            see = f' <span class="see">See: {" · ".join(self.link(x) for x in g.get("see", []))}</span>' if g.get("see") else ""
            out.append(f'<div class="gterm" id="{esc(g["id"])}"><dt>{esc(g["term"])}</dt><dd>{self.inline(g["def"])}{see}</dd></div>')
        out.append("</dl>")
        self.ctx = None
        return self.section("glossary", "Glossary", "\n".join(out), kicker="Reference", tools=False)

    def view_reading(self):
        levels = [("intro", "Introductory: accessible, for a general reader"),
                  ("intermediate", "Intermediate: demanding but non-specialist"),
                  ("advanced", "Advanced: specialist or dense")]
        out = [self.para(self.meta.get("reading_intro", ""))]
        for lv, lname in levels:
            items = [r for r in self.reading if r["difficulty"] == lv]
            by_area = {}
            for r in items:
                by_area.setdefault(r["area"], []).append(r)
            inner = []
            for a in self.areas:
                rs = by_area.get(a["id"])
                if not rs:
                    continue
                lis = []
                for r in sorted(rs, key=lambda r: r["author"]):
                    self.ctx = ("#/reading", "Reading list")
                    src = f' {self.cite([r["source"]])}' if r.get("source") else ""
                    lis.append(f'<li><b>{esc(r["author"])}</b>, <i>{esc(r["title"])}</i> ({esc(r["year"])}){src}<br>'
                               f'<span class="small"><b>Argues:</b> {self.inline(r["argues"])} <b>Best for:</b> {self.inline(r["best"])}</span></li>')
                inner.append(f'<h4>{esc(a["title"])}</h4><ul class="reading">{"".join(lis)}</ul>')
            out.append(self.subsection(f"read-{lv}", f"{lname} ({len(items)})", "".join(inner), open_=(lv == "intro")))
        self.ctx = None
        return self.section("reading", "Reading list", "\n".join(out), kicker="Reference")

    def view_sources(self):
        out = [f'<p>{len(self.src_order)} sources, numbered alphabetically. Inline references such as <sup class="cites">[12]</sup> point here. '
               'The status line records how each source was checked: <b>confirmed</b> means the primary text, abstract or official page was read and says what is claimed; '
               '<b>secondary</b> means it was confirmed through a reliable secondary source; <b>unverified</b> sources are shown with a warning and are not relied on alone.</p><ol class="sources">']
        for k in self.src_order:
            s = self.sources[k]
            n = self.src_num[k]
            url = s.get("url")
            link = f' <a class="ext" href="{esc(url)}" rel="noopener">{esc(shorten(url))}</a>' if url else ""
            st = s.get("status", "UNVERIFIED")
            stc = {"FETCHED-CONFIRMED": "ok", "SECONDARY": "sec"}.get(st, "unv")
            stl = {"ok": "confirmed", "sec": "secondary", "unv": "⚠ unverified"}[stc]
            back = sorted(self.backrefs.get(k, set()), key=lambda x: x[1])
            if not back:
                self.warnings.append(f"source {k} is never cited")
            bl = " · ".join(f'<a href="{h}">{esc(l)}</a>' for h, l in back)
            note = f' <span class="small muted">{esc(s["note"])}</span>' if s.get("note") else ""
            out.append(f'<li id="src-{n}" value="{n}"><span class="cite">{esc(s["cite"])}</span>{link} '
                       f'<span class="st st-{stc}">{stl}</span>{note}'
                       + (f'<br><span class="small cited-by">Cited in: {bl}</span>' if bl else "") + "</li>")
        out.append("</ol>")
        return self.section("sources", "Sources", "\n".join(out), kicker="Reference", tools=False)

    def view_method(self):
        m = self.method
        self.ctx = ("#/method", "Method")
        rub = "".join(f'<li>{self.badge(k)} {esc(d)}</li>' for k, (_c, _l, _i, d) in STRENGTHS.items())
        out = [self.para(m.get("intro", "")), f'<h3 class="h3">Evidence-strength rubric</h3><ul class="legend">{rub}</ul>']
        for sec in m.get("sections", []):
            out.append(self.subsection("m-" + slug(sec["title"]), sec["title"], self.para(sec["body"]), open_=sec.get("open", False)))
        self.ctx = None
        return self.section("method", "Method & verification notes", "\n".join(out), kicker="Reference")

    def view_search(self):
        body = ('<form class="search-big" role="search" onsubmit="return false"><label for="q2" class="vh">Search the atlas</label>'
                '<input id="q2" type="search" placeholder="Search entries, thinkers, glossary, sources…" autocomplete="off"></form>'
                '<p id="search-status" class="muted" aria-live="polite"></p><ol id="search-results" class="results"></ol>')
        return self.section("search", "Search", body, tools=False)

    # ---------- search index ----------
    def search_index(self):
        docs = []
        strip = lambda h: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h)).strip()
        for e in self.entries:
            self.ctx = None
            txt = " ".join([self.inline(e["claim"] if isinstance(e["claim"], str) else " ".join(e["claim"])),
                            " ".join(self.inline(x) for x in e.get("for", [])),
                            " ".join(self.inline(x) for x in e.get("against", [])),
                            " ".join(e.get("proponents", [])), " ".join(e.get("critics", [])),
                            " ".join(e.get("disciplines", []))])
            docs.append({"t": e["title"], "u": f"#/{e['area']}/e-{e['id']}", "k": "Card · " + self.area_by_id.get(e["area"], {}).get("short", ""), "x": strip(txt)})
        for t in self.thinkers:
            docs.append({"t": t["name"], "u": f"#/thinkers/t-{t['id']}", "k": "Thinker", "x": strip(self.inline(t.get("ideas", "")) + " " + self.inline(t.get("critics", "")) + " " + " ".join(t.get("works", [])))})
        for g in self.glossary:
            docs.append({"t": g["term"], "u": f"#/glossary/{g['id']}", "k": "Glossary", "x": strip(self.inline(g["def"]))})
        for t in self.tensions:
            docs.append({"t": t["title"], "u": f"#/tensions/{t['id']}", "k": "Tension", "x": strip(self.para(t.get("summary")) + " ".join(self.para(s["claim"]) for s in t["sides"]) + self.para(t.get("crux")))})
        for g in self.gaps:
            docs.append({"t": g["title"], "u": f"#/gaps/{g['id']}", "k": "Gap", "x": strip(self.para(g["text"]))})
        for a in self.areas:
            docs.append({"t": a["title"], "u": f"#/{a['id']}", "k": "Area", "x": strip(" ".join(self.para(a.get(k)) for k in ("overview", "steelman", "internal_tensions", "cross_tensions", "open_questions")))})
        for r in self.reading:
            docs.append({"t": f'{r["author"]}, {r["title"]}', "u": "#/reading", "k": "Reading", "x": strip(self.inline(r["argues"]) + " " + self.inline(r["best"]))})
        for k in self.src_order:
            docs.append({"t": self.sources[k]["cite"][:120], "u": f"#/sources/src-{self.src_num[k]}", "k": f"Source {self.src_num[k]}", "x": self.sources[k]["cite"]})
        self.backrefs_snapshot = None
        return docs

    # ---------- page ----------
    def nav(self):
        g = []
        g.append('<li><a href="#/map">Map of the territory</a></li>')
        groups = {}
        for a in self.areas:
            groups.setdefault(a.get("group", "Layers of explanation"), []).append(a)
        out = ['<nav class="side-nav" aria-label="Sections"><ul>', "".join(g)]
        for gname, areas in groups.items():
            out.append(f'<li class="grp"><span>{esc(gname)}</span><ul>')
            for a in areas:
                out.append(f'<li><a href="#/{a["id"]}"><span class="num">{esc(a.get("num", ""))}</span> {esc(a["short"])}</a></li>')
            out.append("</ul></li>")
        out.append('<li class="grp"><span>Across the frameworks</span><ul>'
                   '<li><a href="#/tensions">Tensions &amp; contradictions</a></li>'
                   '<li><a href="#/gaps">Gaps: what remains unexplained</a></li>'
                   '<li><a href="#/helps">What helps: the evidence</a></li></ul></li>')
        out.append('<li class="grp"><span>Reference</span><ul>'
                   '<li><a href="#/explore">Explore &amp; filter</a></li>'
                   '<li><a href="#/thinkers">Who\'s who</a></li>'
                   '<li><a href="#/glossary">Glossary</a></li>'
                   '<li><a href="#/reading">Reading list</a></li>'
                   '<li><a href="#/sources">Sources</a></li>'
                   '<li><a href="#/method">Method &amp; verification</a></li></ul></li>')
        out.append("</ul></nav>")
        return "".join(out)

    def render(self):
        views = [self.view_map()]
        views += [self.view_area(a) for a in self.areas]
        views += [self.view_tensions(), self.view_gaps(), self.view_helps(), self.view_thinkers(),
                  self.view_glossary(), self.view_reading(), self.view_method()]
        views.append(self.view_explore())
        views.append(self.view_search())
        # sources last so every backref has been collected
        views.append(self.view_sources())
        backl = {k: sorted([[h, l] for h, l in v if not h.endswith(f"/e-{k}")], key=lambda x: x[1]) for k, v in self.cross_backlinks.items()}
        idx = self.search_index()
        css = (HERE / "site.css").read_text(encoding="utf-8")
        js = (HERE / "site.js").read_text(encoding="utf-8")
        data = json.dumps({"search": idx, "backlinks": backl}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        title = self.meta.get("site_title", "Age of Anguish")
        desc = self.meta.get("description", "")
        return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<style>{css}</style>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="topbar">
  <button type="button" id="navtoggle" aria-controls="sidebar" aria-expanded="false" aria-label="Open navigation">☰</button>
  <a class="brand" href="#/map">{esc(title)}</a>
  <button type="button" id="theme" aria-label="Colour theme: auto" title="Toggle light / dark">◑</button>
</header>
<aside id="sidebar" class="sidebar">
  <div class="side-head"><a class="brand" href="#/map">{esc(title)}</a><p class="tag">{esc(self.meta.get("tagline", ""))}</p></div>
  <form class="search-mini" role="search" onsubmit="return false"><label for="q" class="vh">Search</label>
  <input id="q" type="search" placeholder="Search the atlas…" autocomplete="off"></form>
  {self.nav()}
  <div class="side-foot"><button type="button" id="theme2">Theme: auto</button> <button type="button" id="printall">Print whole site</button></div>
</aside>
<div class="scrim" id="scrim" hidden></div>
<main id="main" tabindex="-1">
{"".join(views)}
<footer class="foot"><p>{self.inline(self.meta.get("footer", ""))}</p></footer>
</main>
<script id="site-data" type="application/json">{data}</script>
<script>{js}</script>
</body>
</html>
"""


def wrap(s, width):
    words, lines, cur = s.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return lines[:3]


def shorten(url):
    u = re.sub(r"^https?://(www\.)?", "", url)
    return u if len(u) <= 60 else u[:57] + "…"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--content", default=str(ROOT / "content"))
    ap.add_argument("--out", default=str(ROOT / "index.html"))
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = ap.parse_args()
    try:
        site = Site(args.content)
        page = site.render()
    except BuildError as ex:
        print(f"BUILD FAILED: {ex}", file=sys.stderr)
        return 1
    for w in site.warnings:
        print(f"warning: {w}", file=sys.stderr)
    errs = sorted(set(site.errors))
    if errs or (args.strict and site.warnings):
        for e in errs:
            print(f"error: {e}", file=sys.stderr)
        print(f"BUILD FAILED with {len(errs)} error(s)", file=sys.stderr)
        return 1
    if re.search(r'<(script|link|img)[^>]+(src|href)="https?://', page):
        print("BUILD FAILED: external resource reference found", file=sys.stderr)
        return 1
    Path(args.out).write_text(page, encoding="utf-8")
    print(f"wrote {args.out}: {len(page) / 1024:.0f} KB, {len(site.entries)} entries, "
          f"{len(site.thinkers)} thinkers, {len(site.sources)} sources, {len(site.glossary)} glossary terms")
    return 0


if __name__ == "__main__":
    sys.exit(main())
