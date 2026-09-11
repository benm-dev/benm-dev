# Connected profile

The README is one connected map. Identity, people and topic branches, commits,
pull requests, issues, and public/private totals share a single SVG composition.
There are no work sections, disclosures, badges, or repository lists.

## What the map means

Solid paths carry the counted activity. Dotted connections describe broad areas
of work: people, systems, software and AI. Those topic connections are
illustrative; the input does not identify collaborators or associate particular
commits with those topics. Circle pulses are public activity; square-ended
pulses are private activity. Each pulse represents a batch, not one record.

The input is the checked-in [`activity.json`](./activity.json), a dated snapshot
of 56 consecutive UTC days. Commit counts cover authored commits on default
branches of accessible owned repositories pushed during the window. Duplicate
commits across forks count once and are public if also present publicly. Pull
requests and issues count authored items opened during the window across
accessible repositories. These rules differ from GitHub's contribution-calendar
rules and do not claim complete lifetime activity.

Only aggregate counts and dates are exported. Repository names, commit IDs,
issue numbers, titles, descriptions, collaborators, and API payloads are absent
from the snapshot. The renderer validates its allowlisted input schema before
writing output. Rendering is offline and never reads credentials.

## How the replay works

[`scripts/render_connections.py`](./scripts/render_connections.py) compiles the
snapshot into SVG paths and CSS keyframes. The 56 days advance in 0.36-second
steps after a 0.8-second lead-in. Cumulative values follow each displayed date;
the 21.46-second sequence plays once and settles on the complete snapshot.

For each day, metric and visibility, up to three pulses share the recorded
count. Integer pulse weights sum exactly to that count. Pulse thickness grows
with the logarithm of its weight; it is not a linear quantitative scale. The
displayed numbers preserve exact totals. Quiet days have no pulses.

The complete snapshot is the default visible SVG markup. Animation temporarily
substitutes dated cumulative frames. Unsupported or disabled CSS animation
leaves the full snapshot visible. The SVG's reduced-motion rule disables
animation, and the README additionally selects a separate still asset for
viewers requesting reduced motion. There is no replay button or JavaScript in
the README.

SVG's [secure animated image mode](https://www.w3.org/TR/SVG/conform.html#secure-animated-mode)
supports declarative animation without scripts. The README embeds standalone
images using the same [`picture` pattern](https://github.com/Platane/snk#dark-mode)
used by animated SVG profile projects. This is different from injecting SVG or
scripts directly into Markdown. GitHub's file viewer and individual clients may
render static previews; the map remains readable in those cases.

## Variants

| Layout | Appearance | Replay | Reduced motion |
| --- | --- | --- | --- |
| Desktop, 736 × 650 | Dark | `map-dark.svg` | `map-still-dark.svg` |
| Desktop, 736 × 650 | Light | `map-light.svg` | `map-still-light.svg` |
| Mobile, 360 × 774 | Dark | `map-dark-mobile.svg` | `map-still-dark-mobile.svg` |
| Mobile, 360 × 774 | Light | `map-light-mobile.svg` | `map-still-light-mobile.svg` |

The mobile source breakpoint is a 640-pixel viewport. Mobile nodes and labels
are repositioned, rather than shrinking the desktop layout wholesale. Color
selection follows the viewer's reported color-scheme preference. Essential
information is also available in the image's text alternative.

## Reproduce and refresh

Requires Python 3.11+, Pillow from `requirements.txt`, and DejaVu Sans at
`/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf` (Debian/Ubuntu package
`fonts-dejavu-core`). The system font is used to measure wrapping; the SVG uses
the same font family with Arial and sans-serif fallbacks.

```bash
python3 -m pip install -r requirements.txt
python3 scripts/render_connections.py
python3 -m unittest discover -s tests -p 'test_render_connections.py'
```

Rendering writes eight SVGs, `README.md`, and
`assets/connections/manifest.json`. The manifest records the input hash, date
window, counts, motion duration, pulse weight total, and hashes of the generated
files. Repeated rendering from unchanged input produces the same bytes in the
same environment. To render somewhere else without changing the profile:

```bash
python3 scripts/render_connections.py --output preview
```

To collect a fresh snapshot using an existing authenticated GitHub CLI session
or an existing `GH_TOKEN`/`GITHUB_TOKEN`, then rebuild:

```bash
python3 scripts/collect_activity.py
python3 scripts/render_connections.py
```

The collector fails on incomplete searches or invalid exports. Review the
aggregate diff and commit the snapshot with generated assets. No scheduled
refresh is installed, and rendering alone never changes the snapshot date.

Older enclosure, sculpture and terminal renderers remain in the repository as
previous experiments. They are not embedded by the current README. Use the
connections renderer above to regenerate the current profile.
