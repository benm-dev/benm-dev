#!/usr/bin/env python3
"""Quiet generative banner for GitHub profile. Seed → SVG filter field."""
from __future__ import annotations
import hashlib, os, datetime as dt

seed = os.environ.get("BANNER_SEED") or (
    dt.datetime.now(dt.timezone.utc).strftime("%Y-%W")
    + "-"
    + os.environ.get("GITHUB_SHA", "benm-dev")
)
digest = hashlib.sha256(seed.encode()).hexdigest()
nums = [int(digest[i : i + 2], 16) for i in range(0, 32, 2)]

# Map bytes → tasteful params (narrow ranges = not chaotic/cringe)
base_hue = 210 + (nums[0] % 40) - 20          # blue–violet band
accent = 160 + (nums[1] % 30)                 # teal-ish
freq = 0.006 + (nums[2] / 255.0) * 0.012
octaves = 3 + (nums[3] % 2)
scale = 18 + (nums[4] % 28)
glow_x = 620 + (nums[5] % 280)
glow_y = 20 + (nums[6] % 80)
glow2_x = 120 + (nums[7] % 200)
glow2_y = 140 + (nums[8] % 40)
bar = 3 + (nums[9] % 3)
sat = 0.35 + (nums[10] / 255.0) * 0.25

def hsl(h, s, l, a=1.0):
    return f"hsl({h:.0f} {s*100:.0f}% {l*100:.0f}% / {a:.3f})"

bg0 = hsl(base_hue, 0.25, 0.05)
bg1 = hsl(base_hue + 12, 0.30, 0.09)
c1 = hsl(base_hue + 20, sat, 0.55, 0.22)
c2 = hsl(accent, sat * 0.9, 0.50, 0.14)
line = hsl(base_hue + 30, 0.55, 0.68, 0.95)
muted = hsl(base_hue, 0.12, 0.62, 1.0)
fg = hsl(base_hue, 0.10, 0.93, 1.0)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="220" viewBox="0 0 1100 220" role="img" aria-label="Benjamin Marshall">
  <title>Benjamin Marshall</title>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{bg0}"/>
      <stop offset="100%" stop-color="{bg1}"/>
    </linearGradient>
    <filter id="field" x="-20%" y="-40%" width="140%" height="180%" color-interpolation-filters="sRGB">
      <feTurbulence type="fractalNoise" baseFrequency="{freq:.5f}" numOctaves="{octaves}" seed="{int(digest[:6], 16) % 10000}" result="noise"/>
      <feGaussianBlur in="noise" stdDeviation="0.6" result="soft"/>
      <feColorMatrix in="soft" type="matrix" values="
        0 0 0 0 0.15
        0 0 0 0 0.25
        0 0 0 0 0.45
        0 0 0 {sat:.3f} 0" result="tint"/>
      <feDiffuseLighting in="soft" lighting-color="{hsl(base_hue+10, 0.4, 0.7)}" surfaceScale="{scale * 0.15:.2f}" result="lit">
        <feDistantLight azimuth="{30 + nums[11] % 60}" elevation="{45 + nums[12] % 25}"/>
      </feDiffuseLighting>
      <feBlend in="lit" in2="tint" mode="screen" result="mix"/>
      <feGaussianBlur in="mix" stdDeviation="8" result="haze"/>
      <feBlend in="haze" in2="SourceGraphic" mode="soft-light"/>
    </filter>
    <radialGradient id="g1" cx="{glow_x}" cy="{glow_y}" r="420" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="{c1}"/>
      <stop offset="100%" stop-color="{c1}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="g2" cx="{glow2_x}" cy="{glow2_y}" r="360" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="{c2}"/>
      <stop offset="100%" stop-color="{c2}" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="1100" height="220" fill="url(#bg)"/>
  <rect width="1100" height="220" filter="url(#field)" opacity="0.85"/>
  <rect width="1100" height="220" fill="url(#g1)"/>
  <rect width="1100" height="220" fill="url(#g2)"/>
  <rect x="0" y="0" width="{bar}" height="220" fill="{line}"/>
  <text x="48" y="96" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Helvetica, Arial, sans-serif" font-size="34" font-weight="600" fill="{fg}" letter-spacing="-0.03em">Benjamin Marshall</text>
  <text x="48" y="132" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Helvetica, Arial, sans-serif" font-size="15" fill="{muted}">Sydney</text>
</svg>
'''

out = os.environ.get("BANNER_OUT", "banner.svg")
with open(out, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"wrote {out} seed={seed!r}")
