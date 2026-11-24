# Blobmoji SVG Normalizer Scripts

These Python scripts are not used as part of the font compilation process. Instead, they are manually executed when necessary to make fixes to issues with the SVGs that cause font compilation to fail.

## picosvg / COLRv1 fixes

- `flatten_clippath_groups.py` — Run before COLRv1 builds if `picosvg` fails with `Bad tag <g>` inside a `<clipPath>`. Handles Inkscape group/powerclip exports (nested `<g>` inside the clipPath) and clip-to-group exports (`<use xlink:href="#someGroup">` inside the clipPath). For group references, filled shapes are copied into the clipPath with composed transforms; the painted group is not moved.
- `strip_dangling_clip_refs.py` — Run if `picosvg` fails with `Expected //svg:clipPath[@id="..."] matches in range(1, 2), 0 results` (Illustrator `SVGID_*` clip leftover after an Inkscape redesign / style-tag inlining).
- `strip_svg_font_elements.py` — Run if `picosvg` fails with `BadElement: /svg[0]/font[0]` (Inkscape leftover SVG 1.1 `<font>` trees after text-to-path).

## General SVG cleanup

- `inject_svg_viewboxes.py` — Adds a root `viewBox` derived from `width` and `height` when it is missing (strips `px` from dimensions). Processes `../svg` in place.
- `scale_svgs.py` — Rescales each SVG under `../svg` into a uniform `viewBox="0 0 128 128"` by wrapping content in a group and applying a scale transform (keeps aspect ratio).
- `strip_width_and_height_tags.py` — Removes root `width` and `height` attributes from SVGs in `../svg` so sizing is driven by `viewBox` only.
- `svg_px_suffix_remover.py` — Strips literal `px` suffixes from numeric attribute values (regex over file text). Writes to a configured input/output folder; supports dry run.
- `svg_style_tag_replacer.py` — Inlines rules from `<style>` blocks onto matching elements and removes the `<style>` tags (requires `pip install lxml cssselect cssutils`). Walks `../svg` in place; helps avoid dangling clip ids and other picosvg issues tied to embedded CSS.

## Text and diagnostics

- `embed_text_as_objects.py` — Uses Inkscape CLI (`--export-text-to-path`) to turn `<text>` into paths, then strips font-related attributes and leftover `<font>` elements. Requires Inkscape and installed fonts; intended for copies or folders that need conversion, not routine in-place runs on the main glyph set unless you intend that.
- `scan_for_text_tags.py` — Reports which SVGs in the `svg` folder still contain `<text>`, `<tspan>`, or `<textPath>` (use before batch text-to-path conversion).