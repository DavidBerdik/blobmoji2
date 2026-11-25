# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Generate nanoemoji config files for Noto-COLRv0 (staged SVGs)."""

from pathlib import Path

from colr_svg_sources import (
    NOTO_FAMILY_NAME,
    NOTO_SVG_DIR,
    NOTO_WAVED_FLAG_SVG_DIR,
    all_colr_svg_paths,
    noflag_colr_svg_paths,
)

_CONFIG_DIR = Path("colrv0")
_STAGED_SVG = _CONFIG_DIR / "staged/svg"
_STAGED_WAVED = _CONFIG_DIR / "staged/waved-svg"


def _rel_staged(svg_path: Path) -> str:
    if svg_path.parent.resolve() == NOTO_SVG_DIR.resolve():
        return f"staged/svg/{svg_path.name}"
    if svg_path.parent.resolve() == NOTO_WAVED_FLAG_SVG_DIR.resolve():
        return f"staged/waved-svg/{svg_path.name}"
    raise ValueError(svg_path)


def _write_config(config_name, output_file, svg_files):
    rel_paths = sorted(_rel_staged(Path(f)) for f in svg_files)
    for rel in rel_paths:
        assert (_CONFIG_DIR / rel).is_file(), f"{rel} not found (run colrv0_stage_svgs.py)"
    svg_list = ",\n    ".join(f'"{f}"' for f in rel_paths)
    with open(_CONFIG_DIR / f"{config_name}.toml", "w", encoding="utf-8") as f:
        f.write(
            f"""
family = "{NOTO_FAMILY_NAME}"
output_file = "{output_file}"
color_format = "glyf_colr_0"
clipbox_quantization = 32
reuse_tolerance = 0.1

[axis.wght]
name = "Weight"
default = 400

[master.regular]
style_name = "Regular"
srcs = [
    {svg_list},
]

[master.regular.position]
wght = 400
"""
        )


def main():
    _CONFIG_DIR.mkdir(exist_ok=True)
    _write_config("all", "NotoColorEmoji.ttf", all_colr_svg_paths())
    _write_config("noflags", "NotoColorEmoji-noflags.ttf", noflag_colr_svg_paths())


if __name__ == "__main__":
    main()