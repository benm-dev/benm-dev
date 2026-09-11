#!/usr/bin/env python3
"""Regenerate profile banner.svg + activity.svg from public events + week seed."""
from __future__ import annotations
import collections, datetime as dt, hashlib, json, subprocess, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

def hsl(h, s, l, a=1.0):
    return f"hsl({h:.1f} {s*100:.1f}% {l*100:.1f}% / {a:.3f})"

def main():
    raw = subprocess.check_output(["gh", "api", "users/benm-dev/events?per_page=100"], text=True)
    events = json.loads(raw)
    by_day = collections.Counter(e["created_at"][:10] for e in events)
    types = collections.Counter(e["type"] for e in events)
    today = dt.date.today()
    days = [(today - dt.timedelta(days=55 - i)).isoformat() for i in range(56)]
    series = [by_day.get(d, 0) for d in days]
    mx = max(series) or 1
    seed = hashlib.sha256(
        (today.strftime("%Y-%W") + "-" + (events[0]["id"] if events else "benm")).encode()
    ).hexdigest()
    nums = [int(seed[i : i + 2], 16) for i in range(0, 40, 2)]
    freq = 0.0055 + (nums[0] / 255) * 0.01
    seed_i = int(seed[:6], 16) % 9000
    hue = 205 + (nums[1] % 35) - 10
    accent = 155 + (nums[2] % 25)

    cols = []
    x = 48
    for i in range(7):
        w = 70 + (nums[3 + i] % 90)
        h = 40 + (nums[10 + i] % 70)
        y = 150 - h
        op = 0.04 + (nums[8 + i] % 10) / 200
        cols.append((x, y, w, h, op))
        x += w + 10

    tiles = []
    for i, (x, y, w, h, op) in enumerate(cols):
        tiles.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" opacity="{op:.3f}">'
            f'<animate attributeName="opacity" values="{op:.3f};{min(op*2.2,0.18):.3f};{op:.3f}" dur="{10+i}s" repeatCount="indefinite"/>'
            f"</rect>"
        )

    banner = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="340" viewBox="0 0 1200 340" role="img" aria-label="Benjamin Marshall">
  <title>Benjamin Marshall</title>
  <desc>Generative field seeded {seed[:12]} · week {today.strftime('%Y-%W')} · abstract tiling · living noise</desc>
  <metadata id="seed">{seed}</metadata>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{hsl(hue,0.28,0.045)}"/>
      <stop offset="55%" stop-color="{hsl(hue+14,0.32,0.08)}"/>
      <stop offset="100%" stop-color="{hsl(hue-8,0.22,0.05)}"/>
    </linearGradient>
    <radialGradient id="a1" cx="78%" cy="8%" r="55%">
      <stop offset="0%" stop-color="{hsl(hue+25,0.55,0.55,0.35)}"/>
      <stop offset="100%" stop-color="{hsl(hue+25,0.55,0.55,0)}"/>
    </radialGradient>
    <radialGradient id="a2" cx="12%" cy="90%" r="50%">
      <stop offset="0%" stop-color="{hsl(accent,0.5,0.45,0.22)}"/>
      <stop offset="100%" stop-color="{hsl(accent,0.5,0.45,0)}"/>
    </radialGradient>
    <filter id="field" x="-30%" y="-50%" width="160%" height="200%" color-interpolation-filters="sRGB">
      <feTurbulence id="noise" type="fractalNoise" baseFrequency="{freq:.5f}" numOctaves="4" seed="{seed_i}" result="n">
        <animate attributeName="baseFrequency" values="{freq:.5f};{freq*1.35:.5f};{freq:.5f}" dur="18s" repeatCount="indefinite"/>
      </feTurbulence>
      <feGaussianBlur in="n" stdDeviation="0.8" result="soft"/>
      <feColorMatrix in="soft" type="matrix" values="0 0 0 0 0.12  0 0 0 0 0.22  0 0 0 0 0.48  0 0 0 0.45 0" result="tint"/>
      <feDiffuseLighting in="soft" lighting-color="{hsl(hue+8,0.45,0.72)}" surfaceScale="4.2" result="lit">
        <feDistantLight azimuth="{40+nums[5]%50}" elevation="{50+nums[6]%20}">
          <animate attributeName="azimuth" values="{40+nums[5]%50};{100+nums[5]%40};{40+nums[5]%50}" dur="22s" repeatCount="indefinite"/>
        </feDistantLight>
      </feDiffuseLighting>
      <feBlend in="lit" in2="tint" mode="screen" result="mix"/>
      <feGaussianBlur in="mix" stdDeviation="10" result="haze"/>
      <feBlend in="SourceGraphic" in2="haze" mode="soft-light"/>
    </filter>
    <linearGradient id="sheen" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#fff" stop-opacity="0.05"/>
      <stop offset="50%" stop-color="#fff" stop-opacity="0"/>
      <stop offset="100%" stop-color="#000" stop-opacity="0.25"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="340" fill="url(#bg)"/>
  <rect width="1200" height="340" filter="url(#field)" opacity="0.9"/>
  <rect width="1200" height="340" fill="url(#a1)"/>
  <rect width="1200" height="340" fill="url(#a2)"/>
  <rect width="1200" height="340" fill="url(#sheen)"/>
  <g id="tiles" fill="{hsl(hue+20,0.4,0.75)}">{''.join(tiles)}</g>
  <rect x="0" y="0" width="3" height="340" fill="{hsl(hue+30,0.6,0.7)}"/>
  <text x="48" y="78" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Helvetica, Arial, sans-serif" font-size="42" font-weight="600" fill="{hsl(hue,0.08,0.95)}" letter-spacing="-0.04em">Benjamin Marshall</text>
  <text x="48" y="112" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Helvetica, Arial, sans-serif" font-size="16" fill="{hsl(hue,0.12,0.62)}">Sydney · systems · clients · tooling</text>
  <text x="48" y="300" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="{hsl(hue,0.15,0.45)}">seed {seed[:16]} · field+light · tile-spiral</text>
</svg>
'''
    (ROOT / "banner.svg").write_text(banner)

    W, H = 1200, 200
    pad_x, pad_y = 48, 36
    plot_w, plot_h = W - pad_x * 2, H - pad_y * 2 - 28
    n = len(series)
    parts = []
    pts = []
    for i, v in enumerate(series):
        x = pad_x + (i + 0.5) / n * plot_w
        t = v / mx
        h = 8 + t * (plot_h * 0.85)
        y = pad_y + 28 + (plot_h - h)
        parts.append(
            f'<rect x="{x-(4+t*8)/2:.2f}" y="{y:.2f}" width="{4+t*8:.2f}" height="{h:.2f}" rx="2" fill="{hsl(hue+15,0.55,0.62,0.08+t*0.55)}"/>'
        )
        pts.append((x, pad_y + 28 + plot_h - h))

    d = f"M {pts[0][0]:.2f},{pts[0][1]:.2f}"
    for i in range(1, len(pts)):
        x0, y0 = pts[i - 1]
        x1, y1 = pts[i]
        d += f" Q {x0:.2f},{y0:.2f} {(x0+x1)/2:.2f},{(y0+y1)/2:.2f}"
    d += f" L {pts[-1][0]:.2f},{pts[-1][1]:.2f}"
    area = d + f" L {pts[-1][0]:.2f},{pad_y+28+plot_h:.2f} L {pts[0][0]:.2f},{pad_y+28+plot_h:.2f} Z"
    top_types = types.most_common(4)
    type_txt = ""
    tx = pad_x
    for name, count in top_types:
        type_txt += f'<text x="{tx}" y="{H-16}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10" fill="{hsl(hue,0.12,0.48)}">{name.replace("Event","")} {count}</text>'
        tx += 140

    activity = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Public activity density">
  <title>Public activity · last {n} days</title>
  <desc>Density field and waveform derived from public GitHub events (not the default contrib graph).</desc>
  <defs>
    <linearGradient id="abg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{hsl(hue,0.25,0.06)}"/>
      <stop offset="100%" stop-color="{hsl(hue+8,0.28,0.09)}"/>
    </linearGradient>
    <linearGradient id="wave" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{hsl(accent,0.6,0.55,0.0)}"/>
      <stop offset="40%" stop-color="{hsl(hue+20,0.65,0.65,0.9)}"/>
      <stop offset="100%" stop-color="{hsl(accent,0.55,0.55,0.2)}"/>
    </linearGradient>
    <linearGradient id="fill" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{hsl(hue+15,0.5,0.55,0.28)}"/>
      <stop offset="100%" stop-color="{hsl(hue+15,0.5,0.55,0)}"/>
    </linearGradient>
  </defs>
  <rect width="{W}" height="{H}" rx="14" fill="url(#abg)" stroke="{hsl(hue,0.2,0.22)}" stroke-width="1"/>
  <text x="{pad_x}" y="28" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="{hsl(hue,0.15,0.5)}" letter-spacing="0.12em">PUBLIC SIGNAL · {n}D · NOT CONTRIB SQUARES</text>
  <g>{''.join(parts)}</g>
  <path d="{area}" fill="url(#fill)"/>
  <path d="{d}" fill="none" stroke="url(#wave)" stroke-width="2.2" stroke-linecap="round">
    <animate attributeName="stroke-opacity" values="0.75;1;0.75" dur="4s" repeatCount="indefinite"/>
  </path>
  {type_txt}
  <text x="{W-pad_x}" y="{H-16}" text-anchor="end" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10" fill="{hsl(hue,0.12,0.42)}">max {mx}/day · seed {seed[:8]}</text>
</svg>
'''
    (ROOT / "activity.svg").write_text(activity)
    (ROOT / "seed.json").write_text(
        json.dumps(
            {
                "seed": seed,
                "week": today.strftime("%Y-%W"),
                "events_sampled": len(events),
                "series_days": n,
                "series_sum": sum(series),
                "top_types": top_types,
            },
            indent=2,
        )
        + "\n"
    )
    print("ok", seed[:16], "sum", sum(series))

if __name__ == "__main__":
    main()
