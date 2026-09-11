<p align="center">
  <img src="https://raw.githubusercontent.com/benm-dev/benm-dev/main/banner.svg" width="100%" alt="Benjamin Marshall — generative field" />
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/benm-dev/benm-dev/main/activity.svg" width="100%" alt="Public activity density field" />
</p>

Systems and clients — remote workstations, declarative hosts, local-first tools. Most of it stays private.

**Stack** · Rust · Swift · Nix · TypeScript · Wayland · Python

```bash
curl -sL https://benm-dev.github.io/card
```

<details>
<summary>How this profile is built</summary>

- **Living field** — SVG `feTurbulence` + diffuse lighting; `baseFrequency` and light azimuth animate (no JS).
- **Tile-spiral** — abstract column geometry (compositor language, no window chrome).
- **Public signal** — last 56 days of *public* GitHub events as a density ribbon + waveform (not the green contrib grid).
- **Seed** — `sha256(iso-week + latest public event id)` written into SVG `<metadata>` and `seed.json`.
- **Dual surface** — same identity as truecolor ANSI via the curl card.
- **Regenerate** — `python3 scripts/gen_all.py` (needs `gh`).

</details>

[site](https://benm-dev.github.io) · [seed.json](./seed.json)
