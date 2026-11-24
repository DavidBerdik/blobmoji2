# Blobmoji SVG Normalizer Scripts

These Python scripts are not used as part of the font compilation process. Instead, they are manually executed when necessary to make fixes to issues with the SVGs that cause font compilation to fail.

- `flatten_clippath_groups.py` — Run before COLRv1 builds if `picosvg` fails with `Bad tag <g>` inside a `<clipPath>` (Inkscape group/powerclip exports).
