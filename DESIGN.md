# Rendering the profile

The header is a small software renderer. It turns a dated, anonymised public and private activity snapshot into a 3D form, then exports images that GitHub can display directly.

## Data to geometry

The input is [`activity.json`](./activity.json): 56 consecutive UTC dates, with public and private daily total counts for commits, pull requests opened and issues opened.

The collector uses the authenticated account's available records. Commit counts cover commits authored by `benm-dev` on the default branches of accessible, owned repositories pushed within the window. Duplicate commit SHAs across forks count once; a commit present in a public repository is classified as public. Pull requests and issues count items authored by `benm-dev` and opened within the window across accessible repositories.

These measures describe the collection scope and differ from GitHub's contribution-calendar rules. They can omit work on unmerged branches, inaccessible repositories, commits attributed to another identity, reviews and other interactions. They are a dated snapshot rather than a live status display.

Only aggregate dates and counts are exported. Repository names, commit IDs, issue numbers, titles, descriptions and API payloads never enter the published snapshot. The seed is a SHA-256 digest of the daily aggregate arrays.

[GitHub commit API](https://docs.github.com/en/rest/commits/commits#list-commits) · [GitHub issue and pull-request search](https://docs.github.com/en/rest/search/search#search-issues-and-pull-requests).

1. Apply `log1p` to the daily counts and normalise by the largest transformed count, with a denominator of at least one.
2. Interpolate the 56 bins onto 168 longitudinal samples, then apply three passes of a circular `[0.25, 0.5, 0.25]` smoothing kernel. Closing the geometry is an artistic operation; it does not infer activity for missing dates.
3. Construct a trefoil centreline with rotation-minimising parallel-transport frames. Distribute the residual rotation around the closed loop to remove the seam. The local tube radius is `0.26 + 0.25 × smoothed_activity`.
4. Build a tube with 32 vertices per cross-section. Compute surface normals from the actual mesh, including changes in radius.
5. Apply seeded orientation, orthographic projection, face culling, depth sorting, diffuse light and a restrained specular highlight. The wire sections mark the 56 daily positions.
6. Supersample the geometry at twice the output resolution and downsample with Lanczos filtering.

The daily totals control thickness. The public/private proportion blends the material between a cool base and copper; days without recorded activity retain the base geometry so the curve stays continuous. The SVG activity panels preserve exact linear daily counts, split by visibility and metric. Each metric uses its own vertical scale.

## Motion and layout

There are 96 frames, 80 ms each: a 7.68-second rotation. The last exported frame precedes the first by one normal angular step, so the loop has no duplicated endpoint or pause. The seed changes the starting orientation, while event counts change the geometry.

The README's `<picture>` element selects among eight header assets:

| Layout | Color scheme | Normal motion | Reduced motion |
| --- | --- | --- | --- |
| Desktop, 1440 × 620 | Light | `hero-light.webp` | `hero-light.png` |
| Desktop, 1440 × 620 | Dark | `hero-dark.webp` | `hero-dark.png` |
| Mobile, 720 × 900 | Light | `hero-light-mobile.webp` | `hero-light-mobile.png` |
| Mobile, 720 × 900 | Dark | `hero-dark-mobile.webp` | `hero-dark-mobile.png` |

The mobile breakpoint is a 600 CSS-pixel viewport. The source order gives reduced-motion images priority. Color selection follows the viewer's reported color-scheme preference. PNGs are also directly available as static alternatives. All image paths are relative so branch previews use their own assets.

GitHub supports the [`picture` element in Markdown](https://github.com/github/docs/blob/main/content/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax.md#the-picture-element). Image selection is native browser behaviour; there is no JavaScript executing inside the README. The WebP contains the rendered frames.

## Reproduce

Requires Python 3.11 or newer. Dependencies are pinned in [`requirements.txt`](./requirements.txt). Typography uses the font bundled with Pillow, so there is no system font or download dependency.

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 scripts/render_profile.py
python3 -m unittest discover -s tests
```

The default command uses only the checked-in snapshot. It writes four PNGs, four animated WebPs, four responsive SVG activity panels and `assets/manifest.json`. The manifest contains a canonical input hash and SHA-256 hashes of the exported assets. These identify the exact output files; encoders on different platforms may produce different compressed bytes.

For a quick preview:

```bash
python3 scripts/render_profile.py --still --output preview
```

For a new public snapshot and render:

```bash
python3 scripts/render_profile.py --refresh
```

Refresh uses an existing authenticated GitHub CLI session, or `GH_TOKEN` / `GITHUB_TOKEN` already present in the local environment. Credentials and repository identifiers stay in the collection process. API errors, incomplete searches and export-schema violations stop the refresh before the snapshot is replaced. Searches exceeding the API's 1,000-result cap fail explicitly.

Run manually or from an existing local runner, review the aggregate diff, then commit the snapshot and assets together. No scheduled GitHub workflow is installed.

## Terminal rendering

```bash
python3 scripts/terminal.py
```

The same mesh runs live in a terminal with Unicode Braille and 24-bit color. Each character holds eight sample points; front-facing geometry is projected into that grid and colored from the same public/private distribution. The renderer uses the alternate screen and restores the cursor on exit. Press Ctrl-C to stop. `--still` emits one frame, and output to a pipe defaults to a still.

This terminal renderer reads the local aggregate snapshot and makes no network requests.

The earlier `scripts/gen_all.py`, root-level banner files, `activity.svg`, `seed.json` and the old terminal card remain as legacy assets for the separate site. The new renderer does not update or deploy that site.
