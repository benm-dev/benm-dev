<p align="center">
  <img src="https://raw.githubusercontent.com/benm-dev/benm-dev/main/banner.webp" width="100%" alt="Benjamin Marshall — animated generative field" />
</p>

# Benjamin Marshall

I build systems and clients: reproducible workstations, remote desktop tools, and local-first software. Based in Sydney; most of my work stays private.

**Stack** · Rust · Swift · Nix · TypeScript · Wayland · Python

## What I'm building

- **zerokelvin** · private, ongoing — my declarative NixOS workstation project. Complete system configuration, Wayland desktops, development environments, and remote access, with an emphasis on reproducible state and deliberate changes.
- **Foldlight** · private, ongoing — a desktop-focused client for foldable Android devices, built on Moonlight Android. Sunshine streaming, touch input, and on-screen typing make the PC usable from a phone. Broader keyboard and desktop integration is still in development.
- **Developer tooling** — application compatibility, agent and IDE integration, and automation around the workstation. I care about tools that work together and changes that can be checked.

The wider goal: one capable desktop, accessible from a laptop or a foldable phone, with readable configuration and clear ownership of each component.

## Exploring

Component-based OS design inspired by Cordis: explicit dependencies, capabilities, and lifecycles for applications and system services. This is ongoing design work; the foundation and integration are still being worked out.

## Public work

- [Microsoft WSL #14081](https://github.com/microsoft/WSL/pull/14081) — proposed fix for loopback endpoint creation in mirrored networking. Currently an open draft PR.

[Explore the interactive field →](https://benm-dev.github.io)

## Public activity

<p align="center">
  <img src="https://raw.githubusercontent.com/benm-dev/benm-dev/main/activity.svg" width="100%" alt="Public GitHub event snapshot shown as a 56-day density ribbon and waveform" />
</p>

A snapshot of sampled public GitHub events across a 56-day window. The generator fetches up to 100 events, so this is a partial view of activity. The data refreshes when the assets are regenerated.

## In your terminal

```bash
curl -fsSL https://benm-dev.github.io/card
```

<details>
<summary>How the profile is built</summary>

### Profile assets

- [`banner.webp`](./banner.webp) — animated generative banner displayed above.
- [`activity.svg`](./activity.svg) — event density ribbon and waveform.
- [`seed.json`](./seed.json) — seed and event summary metadata.
- [`activity.json`](./activity.json) — dated activity series used by the interactive site.

The SVG generator derives its seed from the week and the latest sampled event ID.

### Interactive site

The [site](https://benm-dev.github.io) renders a pointer-reactive noise field in Canvas, with a scanning light, an animated activity panel, a Sydney clock, and an FPS readout. It loads a saved activity snapshot on page load.

[View the site source](https://github.com/benm-dev/benm-dev.github.io).

### Regenerate the SVGs and seed

Requires Python 3 and an authenticated GitHub CLI (`gh`). The Python script uses only the standard library. From the repository root:

```bash
python3 scripts/gen_all.py
```

This overwrites `banner.svg`, `activity.svg`, and `seed.json`. The checked-in script does not regenerate `banner.webp`, `banner.png`, `activity.json`, or the terminal card, and does not sync assets to the site repository. Refresh those separately when updating the full profile.

</details>

[Site](https://benm-dev.github.io) · [Activity data](./activity.json) · [Seed metadata](./seed.json)
