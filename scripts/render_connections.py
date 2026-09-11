#!/usr/bin/env python3
"""Render the connected profile from the checked-in, aggregate-only snapshot.

Offline: no credentials, network access, or publication. Motion is compiled into
standalone SVG/CSS, so the README does not need executable HTML or JavaScript.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from datetime import date
from html import escape
from pathlib import Path

from PIL import ImageFont

from collect_activity import validate

ROOT = Path(__file__).resolve().parents[1]
KINDS = (("commits", "Commits"), ("pull_requests", "PRs opened"), ("issues", "Issues opened"))
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
PALETTES = {
    "dark": dict(bg="#10151b", ink="#e3edf3", muted="#9cb0bd", line="#334856", public="#91d7e8", private="#d6a17b", rim="#7290a1", face="#263946", recess="#17232c"),
    "light": dict(bg="#f4f6f7", ink="#182b38", muted="#536877", line="#b3c4cf", public="#176d8a", private="#955b37", rim="#7a99ac", face="#dbe6ec", recess="#e4ebef"),
}
INTRO = "Connecting people, software and systems."
START = 0.8
DAY_SECONDS = 0.36
DURATION = START + 56 * DAY_SECONDS + 0.5


def label_date(value, year=False):
    return date.fromisoformat(value).strftime("%d %b %Y" if year else "%d %b")


def date_range(snapshot):
    return f"{label_date(snapshot['days'][0])} – {label_date(snapshot['days'][-1], True)}"


def totals(snapshot, day=55):
    metrics = [sum(snapshot["metrics"][kind][vis][:day + 1]) for kind, _ in KINDS for vis in ("public", "private")]
    return {"kinds": [metrics[i] + metrics[i + 1] for i in range(0, 6, 2)],
            "public": sum(metrics[::2]), "private": sum(metrics[1::2]), "total": sum(metrics)}


@dataclass(frozen=True)
class Packet:
    day: int
    kind: int
    visibility: str
    weight: int
    ordinal: int
    count: int


def packets(snapshot):
    """Bound visual density while conserving every record in pulse weights."""
    result = []
    for day in range(56):
        for ki, (kind, _) in enumerate(KINDS):
            for visibility in ("public", "private"):
                n = snapshot["metrics"][kind][visibility][day]
                if not n:
                    continue
                count = min(3, math.ceil(n / 12))
                base, extra = divmod(n, count)
                result.extend(Packet(day, ki, visibility, base + (i < extra), i, count) for i in range(count))
    return result


class SVG:
    def __init__(self, mobile, theme, height, title):
        self.mobile, self.theme = mobile, theme
        self.w, self.h, self.p = (360, height, 22) if mobile else (736, height, 32)
        self.c = PALETTES[theme]
        self.title = title
        self.parts, self.css, self.copy = [], [], []

    def add(self, value):
        self.parts.append(value)

    def text(self, x, y, value, size=15, color="ink", anchor="start", weight=400, depth=False):
        self.copy.append(str(value))
        attrs = f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}"'
        if depth:
            self.add(f'<text x="{x + 1}" y="{y + 1.3}" {attrs} fill="{self.c["rim"]}" opacity=".45" aria-hidden="true">{escape(str(value))}</text>')
        self.add(f'<text x="{x}" y="{y}" {attrs} fill="{self.c.get(color, color)}">{escape(str(value))}</text>')

    def wrap(self, x, y, value, width=None, size=15, color="muted", leading=24):
        font = ImageFont.truetype(FONT, size)
        width = self.w - 2 * self.p if width is None else width
        current = ""
        for word in value.split():
            candidate = f"{current} {word}".strip()
            if current and font.getlength(candidate) > width:
                self.text(x, y, current, size, color)
                y += leading
                current = word
            else:
                current = candidate
        if current:
            self.text(x, y, current, size, color)
        return y + leading

    def line(self, y):
        self.add(f'<path d="M{self.p} {y}H{self.w - self.p}" stroke="{self.c["line"]}"/>')

    def circle(self, x, y, radius, fill="bg", stroke="line", width=1):
        self.add(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{radius}" fill="{self.c.get(fill, fill)}" stroke="{self.c.get(stroke, stroke)}" stroke-width="{width}"/>')

    def finish(self):
        css = "text{font-family:DejaVu Sans,Arial,sans-serif;font-variant-numeric:tabular-nums}.packet,.day-stats{opacity:0}"
        css += "".join(self.css)
        css += "@media(prefers-reduced-motion:reduce){*{animation:none!important}.packet,.day-stats{display:none}}"
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}" role="img" aria-labelledby="title desc">'
                f'<title id="title">{escape(self.title)}</title><desc id="desc">{escape(" ".join(dict.fromkeys(self.copy)))}</desc>'
                f'<style>{css}</style><defs><linearGradient id="metal" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{self.c["face"]}"/><stop offset="1" stop-color="{self.c["recess"]}"/></linearGradient></defs>'
                f'<rect width="100%" height="100%" fill="{self.c["bg"]}"/>' + "".join(self.parts) + "</svg>\n")


def route(a, b):
    middle = (a[1] + b[1]) / 2
    return f"M{a[0]:.2f} {a[1]:.2f}C{a[0]:.2f} {middle:.2f} {b[0]:.2f} {middle:.2f} {b[0]:.2f} {b[1]:.2f}"


def stats(p, snapshot, day, hub, actions, legend_y, date_y):
    values = totals(snapshot, day)
    p.text(hub[0], hub[1] + 65, f"{values['total']:,}", 23, anchor="middle")
    for i, (x, y) in enumerate(actions):
        p.text(x, y, f"{values['kinds'][i]:,}", 25, anchor="middle")
    p.text(p.p + 15, legend_y, f"{values['public']:,} public", 14)
    p.text(p.p + (144 if p.mobile else 155), legend_y, f"{values['private']:,} private", 14)
    p.text(p.w - p.p, date_y, label_date(snapshot["days"][max(day, 0)], True), 13, "muted", "end")


def hero(snapshot, mobile, theme, animated=True):
    p = SVG(mobile, theme, 774 if mobile else 650, "Ben Marshall. " + INTRO + " Recorded GitHub activity: " + date_range(snapshot) + ".")
    p.text(p.p, 33, "BENM-DEV", 12, "muted")
    p.text(p.w - p.p, 33, "SYDNEY", 12, "muted", "end")
    p.text(p.p, 87, "Ben Marshall", 36 if mobile else 43, weight=500, depth=True)
    p.wrap(p.p, 118, INTRO, size=16, leading=25)
    oy, h = (157, 492) if mobile else (131, 420)
    hub = (p.w * .5, oy + h * .47)
    domains = [(p.w * .24, oy + 74), (p.w * .76, oy + 74), (p.w * .16, hub[1] + 108), (p.w * .84, hub[1] + 108)] if mobile else [(p.w * .27, oy + 70), (p.w * .73, oy + 70), (p.w * .22, oy + h * .64), (p.w * .78, oy + h * .64)]
    leaf_labels = [("Users", "Community"), ("Linux", "Networks" if mobile else "Networking"), ("Apps" if mobile else "Interfaces", "Tools" if mobile else "Developer tools"), ("Models" if mobile else "Local models", "Agents")]
    leaves = []
    for i, node in enumerate(domains):
        p.add(f'<path d="{route(hub, node)}" fill="none" stroke="{p.c["line"]}" stroke-width="1.3" stroke-dasharray="3 5"/>')
        for j, shift in enumerate((-39, 39)):
            leaf = (node[0] + (-25 if i % 2 == 0 else 25), node[1] + shift)
            p.add(f'<path d="{route(node, leaf)}" fill="none" stroke="{p.c["line"]}" stroke-width="1" stroke-dasharray="3 5"/>')
            leaves.append((leaf, leaf_labels[i][j]))
    actions = [(p.w * x, oy + h - 42) for x in (.16, .5, .84)]
    paths = [route((hub[0], hub[1] + 92), (x, y - 29)) for x, y in actions]
    for path in paths:
        p.add(f'<path d="{path}" fill="none" stroke="{p.c["line"]}" stroke-width="1.2"/>')
    # The four branches describe areas of work, not inferred collaborators or
    # topic attribution. Only the three lower paths carry measured activity.
    for i, (x, y) in enumerate(domains):
        p.circle(x, y + 1.8, 7, "recess", "line")
        p.circle(x, y, 7, "url(#metal)", "rim")
        p.text(x + (15 if i % 2 == 0 else -15), y + 5, ("People", "Systems", "Software", "AI")[i], 14, anchor="start" if i % 2 == 0 else "end")
    for (x, y), label in leaves:
        p.circle(x, y, 2.8)
        p.text(x, y + 19, label, 12 if mobile else 13, "muted", "middle")
    x, y = hub
    p.circle(x, y + 3, 41, "recess", "line")
    p.circle(x, y, 41, "url(#metal)", "rim")
    p.circle(x, y, 32, "none", "line", .8)
    p.text(x, y + 6, "BM", 19, anchor="middle", depth=True)
    p.text(x, y + 84, "recorded actions", 13, "muted", "middle")
    for i, (ax, ay) in enumerate(actions):
        p.circle(ax, ay - 28, 3.5, "rim", "none")
        p.text(ax, ay + 23, KINDS[i][1], 12 if mobile else 13, "muted", "middle")
    line_y = oy + h + 5
    legend_y = line_y + 31
    date_y = line_y + (58 if mobile else 31)
    p.line(line_y)
    p.circle(p.p + 3, legend_y - 5, 3, "public", "none")
    square_x = p.p + (128 if mobile else 139)
    p.add(f'<rect x="{square_x}" y="{legend_y - 8}" width="6" height="6" fill="{p.c["private"]}"/>')
    p.add('<g class="snapshot">')
    stats(p, snapshot, 55, hub, actions, legend_y, date_y)
    p.add('</g>')
    if mobile:
        p.text(p.p, date_y, "Snapshot through", 13, "muted")
    p.text(p.p, line_y + (86 if mobile else 60), date_range(snapshot) + " · 56 UTC days", 12, "muted")
    p.text(p.p, line_y + (109 if mobile else 83), "Counted activity · illustrative connections", 12, "muted")
    # The static snapshot is the default markup. Animation is an enhancement;
    # disabling CSS animation or requesting reduced motion shows the full totals.
    if animated:
        end = 100 * (START + 56 * DAY_SECONDS) / DURATION
        p.css.append(f'.snapshot{{animation:snapshot {DURATION:.2f}s steps(1,end)}}@keyframes snapshot{{0%,{end - .001:.5f}%{{opacity:0}}{end:.5f}%,100%{{opacity:1}}}}')
        p.add('<g class="day-stats start-stats" aria-hidden="true">')
        stats(p, snapshot, -1, hub, actions, legend_y, date_y)
        p.add('</g>')
        p.css.append(f'.start-stats{{animation:initial {DURATION:.2f}s steps(1,end)}}@keyframes initial{{0%,{100 * START / DURATION - .001:.5f}%{{opacity:1}}{100 * START / DURATION:.5f}%,100%{{opacity:0}}}}')
        for day in range(56):
            start = 100 * (START + day * DAY_SECONDS) / DURATION
            stop = 100 * (START + (day + 1) * DAY_SECONDS) / DURATION
            p.css.append(f'.d{day}{{animation:day{day} {DURATION:.2f}s steps(1,end)}}@keyframes day{day}{{0%,{start - .001:.5f}%{{opacity:0}}{start:.5f}%,{stop - .001:.5f}%{{opacity:1}}{stop:.5f}%,100%{{opacity:0}}}}')
            p.add(f'<g class="day-stats d{day}" aria-hidden="true">')
            stats(p, snapshot, day, hub, actions, legend_y, date_y)
            p.add('</g>')
        for i, packet in enumerate(packets(snapshot)):
            begin = START + packet.day * DAY_SECONDS + packet.ordinal * .035
            stop = begin + DAY_SECONDS - .08
            a, b = 100 * begin / DURATION, 100 * stop / DURATION
            p.css.append(f'.p{i}{{animation:packet{i} {DURATION:.2f}s linear}}@keyframes packet{i}{{0%,{a - .001:.5f}%{{opacity:0;stroke-dashoffset:100}}{a:.5f}%{{opacity:.95;stroke-dashoffset:100}}{b:.5f}%{{opacity:.95;stroke-dashoffset:0}}{b + .001:.5f}%,100%{{opacity:0;stroke-dashoffset:0}}}}')
            p.add(f'<path class="packet p{i}" d="{paths[packet.kind]}" pathLength="100" fill="none" stroke="{p.c[packet.visibility]}" stroke-width="{2 + min(2, math.log1p(packet.weight) / 2):.2f}" stroke-linecap="{"round" if packet.visibility == "public" else "butt"}" stroke-dasharray="1.8 98.2" aria-hidden="true"/>')
    # Keep the image description brief and final-state based, rather than reading
    # all 56 animation frames through assistive technology.
    t = totals(snapshot)
    p.copy = [INTRO, f"{t['total']:,} recorded actions, {t['public']:,} public and {t['private']:,} private.",
              "; ".join(f"{t['kinds'][i]:,} {label.lower()}" for i, (_, label) in enumerate(KINDS)) + ".",
              date_range(snapshot) + ".", "People, systems, software and AI are illustrative topic connections. Pulses represent batches of recorded activity, not individual collaborators."]
    return p


def picture(name, alt, motion=False):
    def asset(theme, mobile, still=False):
        return f'./assets/connections/{name}{"-still" if still else ""}-{theme}{"-mobile" if mobile else ""}.svg'
    sources = []
    modes = ((True, " and (prefers-reduced-motion: reduce)"), (False, "")) if motion else ((False, ""),)
    for still, suffix in modes:
        for media, theme, mobile in (("(max-width: 640px) and (prefers-color-scheme: dark)", "dark", True), ("(max-width: 640px)", "light", True), ("(prefers-color-scheme: dark)", "dark", False), ("", "light", False)):
            condition = media + suffix if media else suffix.removeprefix(" and ")
            if not condition:
                continue
            sources.append(f'<source media="{condition}" srcset="{asset(theme, mobile, still)}"/>')
    return '<picture>\n' + '\n'.join(sources) + f'\n<img src="{asset("light", False)}" width="100%" alt="{escape(alt, quote=True)}"/>\n</picture>'


def readme(snapshot):
    t = totals(snapshot)
    alt = f"Ben Marshall, Sydney. {INTRO} {date_range(snapshot)}: {t['total']:,} recorded actions ({t['public']:,} public, {t['private']:,} private); "
    alt += ", ".join(f"{t['kinds'][i]:,} {label.lower()}" for i, (_, label) in enumerate(KINDS)) + ". Connections are illustrative; no collaborators or repositories are identified. "
    alt += snapshot["scope"] + " " + snapshot["coverage"]
    return picture("map", alt, motion=True) + "\n"


def build(snapshot):
    validate(snapshot)
    files = {}
    for mobile in (False, True):
        for theme in PALETTES:
            variant = f'{theme}{"-mobile" if mobile else ""}.svg'
            for name, panel in (("map", hero(snapshot, mobile, theme)), ("map-still", hero(snapshot, mobile, theme, False))):
                files[f"assets/connections/{name}-{variant}"] = panel.finish()
    files["README.md"] = readme(snapshot)
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT, help="Output project directory; input remains the checked-in activity.json")
    args = parser.parse_args()
    snapshot = json.loads((ROOT / "activity.json").read_text())
    files = build(snapshot)
    manifest = {"schema": 1, "renderer": "scripts/render_connections.py", "input_sha256": hashlib.sha256((ROOT / "activity.json").read_bytes()).hexdigest(), "window": {"from": snapshot["days"][0], "to": snapshot["days"][-1]}, "counts": totals(snapshot), "motion": {"seconds": DURATION, "repeats": 1, "packet_weight_total": sum(p.weight for p in packets(snapshot))}, "files": {name: hashlib.sha256(content.encode()).hexdigest() for name, content in sorted(files.items())}}
    files["assets/connections/manifest.json"] = json.dumps(manifest, indent=2) + "\n"
    for name, content in files.items():
        dest = args.output / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content)
    print(f"Rendered {len(files) - 2} SVGs; {snapshot['records_total']:,} aggregate records; one {DURATION:.2f}s replay.")


if __name__ == "__main__":
    main()
