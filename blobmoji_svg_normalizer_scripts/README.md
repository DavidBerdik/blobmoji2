# Blobmoji SVG Normalizer Scripts

These Python scripts are not used as part of the font compilation process. Instead, they are manually executed when necessary to make fixes to issues with the SVGs that cause font compilation to fail.

- `flatten_clippath_groups.py` — Run before COLRv1 builds if `picosvg` fails with `Bad tag <g>` inside a `<clipPath>`. Handles Inkscape group/powerclip exports (nested `<g>` inside the clipPath) and clip-to-group exports (`<use xlink:href="#someGroup">` inside the clipPath). For group references, filled shapes are copied into the clipPath with composed transforms; the painted group is not moved.
- `strip_svg_font_elements.py` — Run if `picosvg` fails with `BadElement: /svg[0]/font[0]` (Inkscape leftover SVG fonts after text-to-path).
- `strip_dangling_clip_refs.py` — Run if `picosvg` fails with `Expected //svg:clipPath[@id="..."] matches in range(1, 2), 0 results` (Illustrator `SVGID_*` clip leftover after an Inkscape redesign / style-tag inlining).
