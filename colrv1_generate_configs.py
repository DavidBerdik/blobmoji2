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

# Generate config files for Noto-COLRv1

from nanoemoji.util import rel
from pathlib import Path

from colr_svg_sources import (
    NOTO_FAMILY_NAME,
    all_colr_svg_paths,
    noflag_colr_svg_paths,
)

_CONFIG_DIR = Path("colrv1")


def _write_config(config_name, output_file, svg_files):
    svg_files = [rel(_CONFIG_DIR, Path(f)) for f in svg_files]
    config_file = f"{config_name}.toml"
    for svg_file in svg_files:
        assert _CONFIG_DIR.joinpath(
            svg_file
        ).is_file(), f"{svg_file} not found relative to {_CONFIG_DIR}"
    svg_list = ",\n    ".join(f'"{f}"' for f in sorted(svg_files)).rstrip()
    with open(_CONFIG_DIR / config_file, "w") as f:
        f.write(
            f"""
family = "{NOTO_FAMILY_NAME}"
output_file = "{output_file}"
color_format = "glyf_colr_1"
clipbox_quantization = 32

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


def _write_all_noto_configs():
    _write_config("all", "NotoColorEmoji.ttf", all_colr_svg_paths())


def _write_noto_noflag_configs():
    _write_config("noflags", "NotoColorEmoji-noflags.ttf", noflag_colr_svg_paths())


def main():
    _write_all_noto_configs()
    _write_noto_noflag_configs()


if __name__ == "__main__":
    main()
