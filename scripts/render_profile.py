#!/usr/bin/env python3
"""Render an anonymised activity snapshot as a rotating, data-shaped trefoil.

Offline by default. --refresh uses existing local GitHub authentication.
The exported snapshot contains aggregate counts only.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import pathlib

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from collect_activity import collect, validate

ROOT = pathlib.Path(__file__).resolve().parents[1]
TAU = math.tau
THEMES = {
    "dark": {"bg": (13, 17, 23), "fg": (233, 237, 239),
             "muted": (139, 148, 158), "rule": (45, 51, 59),
             "surface": (95, 120, 130), "wire": (203, 223, 222),
             "accent": (207, 190, 159)},
    "light": {"bg": (255, 255, 255), "fg": (31, 35, 40),
              "muted": (101, 109, 118), "rule": (216, 222, 228),
              "surface": (109, 151, 155), "wire": (39, 91, 94),
              "accent": (135, 98, 53)},
}


def normalize(v):
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-12)


def geometry(snapshot, rings=168, sides=32):
    """Trefoil tube with closed parallel-transport frames and data-shaped radii.

    There are three longitudinal samples per day. Smoothing is periodic solely
    to close the sculpture; it is not an estimate of missing activity.
    """
    t = np.arange(rings) * TAU / rings
    centre = np.stack(((2 + .64*np.cos(3*t))*np.cos(2*t),
                       (2 + .64*np.cos(3*t))*np.sin(2*t),
                       .92*np.sin(3*t)), axis=-1)
    tangent = normalize(np.roll(centre, -1, axis=0)-np.roll(centre, 1, axis=0))
    # Rotation-minimising frames avoid the abrupt twists a Frenet frame can
    # develop near low curvature. Distribute loop holonomy to close the seam.
    def transport(n, previous, current):
        axis = np.cross(previous, current)
        sine = np.linalg.norm(axis)
        cosine = np.clip(previous @ current, -1, 1)
        if sine < 1e-12:
            return n.copy()
        axis /= sine
        return normalize(n*cosine + np.cross(axis, n)*sine + axis*(axis@n)*(1-cosine))

    normal = np.empty_like(tangent)
    reference = np.eye(3)[np.argmin(abs(tangent[0]))]
    normal[0] = normalize(np.cross(tangent[0], reference))
    for i in range(1, rings):
        normal[i] = transport(normal[i-1], tangent[i-1], tangent[i])
    closed = transport(normal[-1], tangent[-1], tangent[0])
    residual = math.atan2(tangent[0] @ np.cross(closed, normal[0]), closed @ normal[0])
    correction = residual*np.arange(rings)/rings
    normal = normal*np.cos(correction)[:, None] + np.cross(tangent, normal)*np.sin(correction)[:, None]
    binormal = normalize(np.cross(tangent, normal))
    counts = np.log1p(np.asarray(snapshot["series"], dtype=float))
    counts /= max(float(counts.max()), 1)
    activity = np.interp(np.arange(rings)/3, np.arange(57), np.r_[counts, counts[0]])
    for _ in range(3):
        activity = .25*np.roll(activity, 1) + .5*activity + .25*np.roll(activity, -1)
    radius = .26 + .25*activity
    v = np.arange(sides)*TAU/sides
    radial = normal[:, None, :]*np.cos(v)[None, :, None] + binormal[:, None, :]*np.sin(v)[None, :, None]
    mesh = centre[:, None, :] + radius[:, None, None]*radial
    longitudinal = np.roll(mesh, -1, axis=0)-np.roll(mesh, 1, axis=0)
    transverse = np.roll(mesh, -1, axis=1)-np.roll(mesh, 1, axis=1)
    surface_normals = normalize(np.cross(transverse, longitudinal))
    if np.mean(np.sum(surface_normals*radial, axis=-1)) < 0:
        surface_normals *= -1
    private_share = np.divide(snapshot["private_series"], snapshot["series"], out=np.zeros(56), where=np.asarray(snapshot["series"]) > 0)
    share = np.interp(np.arange(rings)/3, np.arange(57), np.r_[private_share, private_share[0]])
    return mesh, surface_normals, activity, share


def rotation(phase, seed):
    # The first seed bytes choose a reproducible initial orientation.
    yaw = phase + .15*math.sin(int(seed[:4], 16)/65535*TAU)
    pitch = .65
    roll = -.28
    cy, sy, cp, sp, cr, sr = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch), math.cos(roll), math.sin(roll)
    y = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    x = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    z = np.array([[cr, -sr, 0], [sr, cr, 0], [0, 0, 1]])
    return z @ x @ y


def font(size):
    # Pillow's bundled Aileron font: the output needs no system font install.
    return ImageFont.load_default(size=size)


def text(draw, xy, value, size, fill):
    draw.text(xy, value, font=font(size), fill=fill, anchor="lt")


def blend(a, b, t):
    return tuple(int(x+(y-x)*t) for x, y in zip(a, b))


def frame(snapshot, mesh_data, phase, theme, mobile=False):
    palette = THEMES[theme]
    width, height = (720, 900) if mobile else (1440, 620)
    image = Image.new("RGB", (width, height), palette["bg"])
    draw = ImageDraw.Draw(image)
    margin = 44 if mobile else 56
    text(draw, (margin, 40), "benm-dev", 22, palette["muted"])
    if mobile:
        text(draw, (margin, 94), "Benjamin", 80, palette["fg"])
        text(draw, (margin, 180), "Marshall", 80, palette["fg"])
        text(draw, (margin, 289), "Systems, clients & tools.", 25, palette["muted"])
        cx, cy, scale = 360, 575, 82
    else:
        text(draw, (margin, 161), "Benjamin", 110, palette["fg"])
        text(draw, (margin, 277), "Marshall", 110, palette["fg"])
        text(draw, (margin, 426), "Systems, clients & tools.", 28, palette["muted"])
        cx, cy, scale = 1080, 285, 86
    # Render geometry separately so edges can be supersampled without soft text.
    ss = 2
    gw, gh = (650, 510) if mobile else (660, 530)
    canvas = Image.new("RGB", (gw*ss, gh*ss), palette["bg"])
    painter = ImageDraw.Draw(canvas)
    mesh, normals, activity, private_share = mesh_data
    # A spherical bound guarantees no clipping at any rotation or event mix.
    scale = min(scale, (min(gw, gh)/2-8)/float(np.linalg.norm(mesh, axis=-1).max()))
    transform = rotation(phase, snapshot["seed"])
    vertices = mesh @ transform.T
    normals = normals @ transform.T
    # Orthographic projection keeps apparent size and data geometry stable.
    xy = vertices[..., :2] * [scale*ss, -scale*ss] + [gw*ss/2, gh*ss/2]
    ring_count, side_count = mesh.shape[:2]
    light = normalize(np.array([-.45, .65, 1.0]))
    faces = []
    for i in range(ring_count):
        ni = (i+1) % ring_count
        for j in range(side_count):
            nj = (j+1) % side_count
            indices = ((i,j), (ni,j), (ni,nj), (i,nj))
            n = normalize(sum(normals[a,b] for a,b in indices))
            if n[2] < -.12:
                continue
            depth = sum(vertices[a,b,2] for a,b in indices)/4
            faces.append((depth, i, j, n, indices))
    faces.sort(key=lambda item: item[0])
    for depth, i, j, n, indices in faces:
        points = [tuple(xy[a,b]) for a,b in indices]
        diffuse = max(float(n @ light), 0)
        private_surface = (139, 106, 81) if theme == "dark" else (172, 127, 91)
        private_wire = (229, 190, 151) if theme == "dark" else (127, 75, 37)
        material = blend(palette["surface"], private_surface, float(private_share[i]))
        wire = blend(palette["wire"], private_wire, float(private_share[i]))
        surface = blend(palette["bg"], material, .25+.72*diffuse)
        specular = max(float(n @ normalize(light + [0, 0, 1])), 0)**28
        surface = blend(surface, wire, .55*specular)
        painter.polygon(points, fill=surface)
        if i % 3 == 0:  # One visible cross-section for each of the 56 dates.
            ink = blend(material, wire, .28+.66*diffuse)
            painter.line([points[0], points[3]], fill=ink, width=2)
        if j % 5 == 0:
            ink = blend(surface, wire, .22+.23*diffuse)
            painter.line([points[0], points[1]], fill=ink, width=1)
        if i % 3 == 0 and activity[i] > .2:
            ink = blend(palette["surface"], palette["accent"], .35+.55*diffuse)
            painter.line([points[0], points[3]], fill=ink, width=2)
    canvas = canvas.resize((gw, gh), Image.Resampling.LANCZOS)
    image.paste(canvas, (int(cx-gw/2), int(cy-gh/2)))
    draw = ImageDraw.Draw(image)
    if mobile:
        draw.line((margin, 825, width-margin, 825), fill=palette["rule"], width=1)
        text(draw, (margin, 848), "Sydney, Australia", 20, palette["muted"])
        text(draw, (395, 848), "56 daily sections", 20, palette["muted"])
    else:
        draw.line((margin, 548, width-margin, 548), fill=palette["rule"], width=1)
        text(draw, (margin, 574), "Sydney, Australia", 20, palette["muted"])
        text(draw, (915, 574), "Public + private / 56 days", 20, palette["muted"])
    return image


def timeline(snapshot, theme, mobile=False):
    p = THEMES[theme]
    color = lambda k: '#%02x%02x%02x' % p[k]
    private_color = '#d6ae87' if theme == 'dark' else '#975d34'
    public_color = '#a9d1d2' if theme == 'dark' else '#32777c'
    width, height = (720, 1010) if mobile else (1440, 445)
    margin = 44 if mobile else 56
    pieces = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
              '<title id="title">Public and private activity, aggregated</title>',
              f'<desc id="desc">{snapshot["records_total"]} records in a 56-day snapshot. Public: {sum(snapshot["public_series"])}. Private: {sum(snapshot["private_series"])}. Commit, pull request and issue counts follow the documented collection scope.</desc>',
              f'<rect width="{width}" height="{height}" fill="{color("bg")}"/>']
    def label(x, y, value, size=20, fill=None, anchor='start'):
        pieces.append(f'<text x="{x}" y="{y}" fill="{fill or color("fg")}" font-family="DejaVu Sans,Arial,sans-serif" font-size="{size}" text-anchor="{anchor}">{html.escape(str(value))}</text>')
    label(margin, 45, 'Public + private activity', 25)
    label(width-margin, 79 if mobile else 45, 'Captured '+snapshot['generated_at'][:10], 18, color('muted'), 'end')
    for row, (key, name) in enumerate((('commits', 'Commits'), ('pull_requests', 'Pull requests opened'), ('issues', 'Issues opened'))):
        x = margin if mobile else margin+row*450
        y = 140+row*275 if mobile else 110
        panel_width = 632 if mobile else 424
        metric = snapshot['metrics'][key]
        public, private = metric['public'], metric['private']
        total = sum(public)+sum(private)
        label(x, y, name, 23, color('muted'))
        label(x, y+75, f'{total:,}', 64)
        label(x+155, y+48, f'{sum(public):,} public', 20, public_color)
        label(x+155, y+75, f'{sum(private):,} private', 20, private_color)
        base = y+206
        maximum = max(max(a+b for a,b in zip(public,private)),1)
        step = panel_width/56
        for i, (a,b) in enumerate(zip(public,private)):
            px = x+i*step
            hp, hv = a/maximum*95, b/maximum*95
            pieces.append(f'<line x1="{px:.2f}" y1="{base+1}" x2="{px+step*.52:.2f}" y2="{base+1}" stroke="{color("rule")}"/>')
            if b:
                pieces.append(f'<rect x="{px:.2f}" y="{base-hv:.2f}" width="{step*.6:.2f}" height="{hv:.2f}" rx="1" fill="{private_color}"><title>{snapshot["days"][i]}: {b} private</title></rect>')
            if a:
                pieces.append(f'<rect x="{px:.2f}" y="{base-hv-hp:.2f}" width="{step*.6:.2f}" height="{hp:.2f}" rx="1" fill="{public_color}"><title>{snapshot["days"][i]}: {a} public</title></rect>')
    footer = height-50
    pieces.append(f'<line x1="{margin}" y1="{footer-26}" x2="{width-margin}" y2="{footer-26}" stroke="{color("rule")}"/>')
    label(margin, footer+5, snapshot['days'][0]+' — '+snapshot['days'][-1], 18, color('muted'))
    label(width-margin, footer+5, 'Daily counts / UTC', 18, color('muted'), 'end')
    pieces.append('</svg>')
    return '\n'.join(pieces)+'\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Collect authenticated public and private activity before rendering")
    parser.add_argument("--still", action="store_true", help="Render only PNG previews and SVG timelines")
    parser.add_argument("--frames", type=int, default=96)
    parser.add_argument("--output", type=pathlib.Path, default=ROOT/"assets")
    args = parser.parse_args()
    if not 2 <= args.frames <= 240:
        parser.error("--frames must be between 2 and 240")
    snapshot = collect() if args.refresh else validate(json.loads((ROOT/"activity.json").read_text()))
    args.output.mkdir(parents=True, exist_ok=True)
    mesh = geometry(snapshot)
    outputs = []
    for theme in THEMES:
        for mobile in (False, True):
            stem = f'hero-{theme}' + ('-mobile' if mobile else '')
            still = frame(snapshot, mesh, 0, theme, mobile)
            still.save(args.output/f'{stem}.png', optimize=True)
            outputs.append(f'{stem}.png')
            if not args.still:
                frames = [still]
                frames.extend(frame(snapshot, mesh, i*TAU/args.frames, theme, mobile) for i in range(1, args.frames))
                frames[0].save(args.output/f'{stem}.webp', save_all=True, append_images=frames[1:],
                               duration=80, loop=0, quality=80, method=4, minimize_size=True)
                outputs.append(f'{stem}.webp')
            print(f'rendered {stem}', flush=True)
        for mobile in (False, True):
            name = f'activity-{theme}' + ('-mobile' if mobile else '') + '.svg'
            (args.output/name).write_text(timeline(snapshot, theme, mobile))
            outputs.append(name)
    if args.refresh:
        (ROOT/"activity.json").write_text(json.dumps(snapshot, indent=2)+'\n')
    manifest = {
        "snapshot_sha256": hashlib.sha256(json.dumps(snapshot, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
        "seed": snapshot["seed"], "captured_at": snapshot["generated_at"],
        "records_total": snapshot["records_total"], "public": sum(snapshot["public_series"]), "private": sum(snapshot["private_series"]),
        "window": [snapshot["days"][0], snapshot["days"][-1]],
        "geometry": {"curve": "trefoil", "frame": "parallel transport with distributed holonomy correction", "daily_sections": 56, "longitudinal_samples": 168, "tube_sides": 32,
                     "radius_mapping": "0.26 + 0.25 * periodic_smooth(log1p(count) / max(1, max(log1p(count))))"},
        "animation": {"frames": args.frames, "duration_ms": args.frames*80, "camera": "orthographic"},
        "assets": {name: hashlib.sha256((args.output/name).read_bytes()).hexdigest() for name in outputs},
    }
    (args.output/"manifest.json").write_text(json.dumps(manifest, indent=2)+'\n')
    print('done', flush=True)


if __name__ == "__main__":
    main()
