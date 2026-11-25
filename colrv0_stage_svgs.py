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

"""Stage SVGs for COLRv0 nanoemoji build (copy, flatten gradients, picosvg, merge)."""

from __future__ import annotations

import argparse
import logging
import shutil
import sys
from pathlib import Path

from lxml import etree
from picosvg.svg import SVG

from colr_svg_sources import NOTO_SVG_DIR, NOTO_WAVED_FLAG_SVG_DIR, all_colr_svg_paths
from colrv0_svg_prep import load_and_prepare_svg

STAGED_ROOT = Path("colrv0/staged")
STAGED_SVG = STAGED_ROOT / "svg"
STAGED_WAVED = STAGED_ROOT / "waved-svg"

log = logging.getLogger(__name__)


def _dest_for_source(src: Path) -> Path:
    if src.parent.resolve() == NOTO_SVG_DIR.resolve():
        return STAGED_SVG / src.name
    if src.parent.resolve() == NOTO_WAVED_FLAG_SVG_DIR.resolve():
        return STAGED_WAVED / src.name
    raise ValueError(f"Unexpected svg path: {src}")


def stage_one(
    src: Path,
    dest: Path,
    *,
    non_consecutive: bool = True,
    snap_grid: float | None = None,
    disjoint_same_paint: bool = False,
) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    work = dest.with_suffix(".work.svg")
    shutil.copy2(src, work)
    try:
        root = load_and_prepare_svg(str(work))
        etree.ElementTree(root).write(
            work, encoding="utf-8", xml_declaration=True, pretty_print=False
        )
        svg = SVG.parse(work).topicosvg()
        from colrv0_merge_paths import (
            clip_and_drop_empty,
            merge_shapes_for_colrv0,
            rebuild_svg_with_shapes,
        )

        shapes = tuple(svg.shapes())
        allow_non_consecutive = non_consecutive and len(shapes) <= 120
        is_waved_flag = dest.parent.name == "waved-svg"
        merged_shapes = merge_shapes_for_colrv0(
            shapes,
            non_consecutive=allow_non_consecutive,
            snap_grid=snap_grid,
            disjoint_same_paint=disjoint_same_paint and not is_waved_flag,
            disjoint_bbox_only=is_waved_flag,
            waved_flag_merge=is_waved_flag,
        )
        merged = clip_and_drop_empty(rebuild_svg_with_shapes(svg, merged_shapes))
        merged.remove_empty_subpaths(inplace=True)
        if not tuple(merged.shapes()):
            raise ValueError("staged SVG has no drawable paths")
        dest.write_text(merged.tostring(), encoding="utf-8")
    finally:
        if work.exists():
            work.unlink()


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--snap-grid",
        type=float,
        default=None,
        help="Optional coordinate snap grid (COLRv0 rung C)",
    )
    parser.add_argument(
        "--no-non-consecutive-merge",
        action="store_true",
        help="Only merge consecutive same-paint paths",
    )
    parser.add_argument(
        "--disjoint-same-paint-merge",
        action="store_true",
        help="Also cluster and union non-overlapping same-paint paths (slow on flags)",
    )
    args = parser.parse_args(argv)

    if STAGED_ROOT.exists():
        shutil.rmtree(STAGED_ROOT)
    STAGED_SVG.mkdir(parents=True)
    STAGED_WAVED.mkdir(parents=True)

    paths = all_colr_svg_paths()
    failures = []
    for i, src in enumerate(paths):
        dest = _dest_for_source(src)
        try:
            stage_one(
                src,
                dest,
                non_consecutive=not args.no_non_consecutive_merge,
                snap_grid=args.snap_grid,
                disjoint_same_paint=args.disjoint_same_paint_merge,
            )
        except Exception as e:
            log.error("Failed %s: %s", src, e)
            failures.append((src, str(e)))
        if (i + 1) % 200 == 0:
            log.info("Staged %d / %d", i + 1, len(paths))
    log.info("Staged %d SVGs to %s", len(paths) - len(failures), STAGED_ROOT)
    if failures:
        for src, err in failures[:20]:
            log.error("  %s: %s", src, err)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())