<p align="center">
  <img src="https://raw.githubusercontent.com/benm-dev/benm-dev/main/banner.webp" width="100%" alt="Benjamin Marshall — living generative field" />
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/benm-dev/benm-dev/main/activity.svg" width="100%" alt="Public activity density field" />
</p>

<p align="center">
  <b>Living version</b> (pointer-reactive field + live signal) → <a href="https://benm-dev.github.io">benm-dev.github.io</a>
</p>

Systems and clients — remote workstations, declarative hosts, local-first tools. Most of it stays private.

**Stack** · Rust · Swift · Nix · TypeScript · Wayland · Python

```bash
curl -sL https://benm-dev.github.io/card
```

<details>
<summary>How this is built (not static)</summary>

### Profile (README)
- **Animated WebP banner** — 36-frame fBm noise field + aurora + breathing tile-spiral, seeded from \`sha256(iso-week + latest public event id)\`. GitHub freezes SVG SMIL in the README, so motion is baked into WebP.
- **Activity SVG** — 56-day public-event density ribbon + waveform (not contrib squares), from the GitHub Events API.
- **seed.json / activity.json** — machine-readable seed + series for regenerators and the live site.

### Live site
- Fullscreen **pointer-reactive fBm field** (Canvas, continuous).
- **Scrolling scan** + light that follows the cursor.
- **Public signal panel** animates the same 56-day series with a moving playhead.
- Sydney clock · FPS · truecolor \`/card\` for terminals.

### Regenerate
\`\`\`bash
python3 scripts/gen_all.py          # svg + json
# animated webp via local tooling (Pillow/numpy) when available
\`\`\`

</details>

[site](https://benm-dev.github.io) · [activity.json](./activity.json) · [seed.json](./seed.json)
