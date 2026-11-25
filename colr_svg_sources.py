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

"""Shared SVG input lists for COLRv1 and COLRv0 nanoemoji builds."""

from pathlib import Path

NOTO_FAMILY_NAME = "Noto Color Emoji"
NOTO_SVG_DIR = Path("svg")
REGIONAL_INDICATORS = frozenset(
    NOTO_SVG_DIR / f"emoji_u{i:x}.svg" for i in range(0x1F1E6, 0x1F1FF + 1)
)
NOTO_WAVED_FLAG_SVG_DIR = Path("third_party/region-flags/waved-svg")
NOTO_SUBDIVISION_FLAGS = (
    NOTO_WAVED_FLAG_SVG_DIR / "emoji_u1f3f4_e0067_e0062_e0065_e006e_e0067_e007f.svg",
    NOTO_WAVED_FLAG_SVG_DIR / "emoji_u1f3f4_e0067_e0062_e0073_e0063_e0074_e007f.svg",
    NOTO_WAVED_FLAG_SVG_DIR / "emoji_u1f3f4_e0067_e0062_e0077_e006c_e0073_e007f.svg",
)

COLRV0_LIMIT = 65535


def all_colr_svg_paths() -> tuple[Path, ...]:
    """All emoji SVGs plus waved region flags (full font)."""
    regular = tuple(NOTO_SVG_DIR.glob("*.svg"))
    flags = tuple(NOTO_WAVED_FLAG_SVG_DIR.glob("*.svg"))
    dups = {p.name for p in regular} & {p.name for p in flags}
    if dups:
        raise ValueError(f"Flags *and* regular have duplicate names: {dups}")
    return regular + flags


def noflag_colr_svg_paths() -> tuple[Path, ...]:
    """Emoji SVGs without regional-indicator letters, plus subdivision flags."""
    svgs = tuple(p for p in NOTO_SVG_DIR.glob("*.svg") if p not in REGIONAL_INDICATORS)
    return svgs + NOTO_SUBDIVISION_FLAGS