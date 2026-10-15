# Maintaining the builder’s console

The profile uses repository-owned SVGs. No external image/statistics API is needed
when someone views it. GitHub still caches images; daily updates are not real-time.

- `assets/portrait-source.jpg` is Dmitry’s public GitHub avatar, downloaded with his
  approval for this profile. The renderer uses a hand-traced silhouette for this
  photo; update the trace as well when replacing it.
- `scripts/render_profile.py --portrait` regenerates desktop/mobile console SVGs.
  Only this option needs Pillow (`python3 -m pip install Pillow`).
- `python3 scripts/render_profile.py --fetch` downloads the unauthenticated public
  GitHub contribution calendar, stores daily intensity levels in
  `data/activity.json`, and regenerates the skyline.
- Without `--fetch`, rendering uses the checked-in snapshot, making it reproducible.
- The skyline represents contributions visible on the public profile, not commit
  counts, working hours, productivity, project revenue or live service health.
- If GitHub changes its calendar format or a fetch fails, the workflow fails without
  committing replacement data. Existing assets remain available.
- Animation runs once and respects `prefers-reduced-motion`. There is no JavaScript
  in the images. Native text below the console preserves essential information.
- SVG links are not interactive when embedded as images. Do not label decorative
  controls as clickable buttons.

The daily workflow commits only changed activity data and its SVG using GitHub’s
Actions bot. Human changes use `Dmitry Siemenov <moxnrl@gmail.com>` and account `mxnr`.

Inspired by the terminal/portrait approach on [navi3582’s profile](https://github.com/navi3582),
with an original renderer, layout and assets. No code or artwork was copied.
