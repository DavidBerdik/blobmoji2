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

"""Estimate COLRv0 layer and glyph budget before nanoemoji compile."""

from __future__ import annotations

import argparse
import hashlib
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from lxml import etree
from picosvg.svg import SVG

from colr_svg_sources import COLRV0_LIMIT, NOTO_WAVED_FLAG_SVG_DIR, all_colr_svg_paths
from colrv0_merge_paths import (
    count_paths_in_svg,
    merge_shapes_for_colrv0,
    paint_key,
)
from colrv0_svg_prep import local_name, load_and_prepare_svg

BLOCKER_TAGS = frozenset({"mask", "filter", "text", "tspan", "textPath", "image"})


def scan_blockers(path: Path) -> List[str]:
    issues = []
    tree = etree.parse(str(path))
    root = tree.getroot()
    for el in root.iter():
        tag = local_name(el.tag)
        if tag in BLOCKER_TAGS:
            if tag == "image":
                img_id = el.get("id")
                # Only report images outside defs or referenced
                parent_chain = []
                p = el.getparent()
                while p is not None:
                    parent_chain.append(local_name(p.tag))
                    p = p.getparent()
                if "defs" not in parent_chain:
                    issues.append(f"<image> outside defs at {path.name}")
            else:
                issues.append(f"<{tag}> in {path.name}")
        if tag == "clipPath":
            for child in el:
                if local_name(child.tag) == "g":
                    issues.append(f"nested <g> in clipPath in {path.name}")
                    break
    return issues


def process_file_like_stage(
    path: Path,
    *,
    non_consecutive: bool = True,
    snap_grid: Optional[float] = None,
) -> Tuple[int, int, int, List[str]]:
    """Return raw_paths, merged_paths, path_hashes for unique outline estimate."""
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        root = load_and_prepare_svg(str(path))
        etree.ElementTree(root).write(
            str(tmp_path), encoding="utf-8", xml_declaration=True
        )
        svg = SVG.parse(str(tmp_path)).topicosvg()
        raw = count_paths_in_svg(svg)
        merged_shapes = merge_shapes_for_colrv0(
            tuple(svg.shapes()),
            non_consecutive=non_consecutive,
            snap_grid=snap_grid,
        )
        merged = len(merged_shapes)
        hashes = [hashlib.sha256(s.d.encode()).hexdigest() for s in merged_shapes]
        return raw, merged, merged, hashes
    finally:
        tmp_path.unlink(missing_ok=True)


def measure_sources(
    paths: Tuple[Path, ...],
    *,
    staged_dir: Optional[Path] = None,
    snap_grid: Optional[float] = None,
) -> Dict:
    total_raw = 0
    total_merged = 0
    per_glyph: List[Tuple[str, int, int, bool]] = []
    all_hashes: List[str] = []
    blockers: List[str] = []
    gradient_files = 0

    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        if "linearGradient" in text or "radialGradient" in text:
            gradient_files += 1
        blockers.extend(scan_blockers(path))
        if staged_dir:
            if path.parent.name == "waved-svg" or "waved-svg" in path.as_posix():
                measure_path = staged_dir / "waved-svg" / path.name
            else:
                measure_path = staged_dir / "svg" / path.name
            if not measure_path.is_file():
                raise FileNotFoundError(f"Missing staged file {measure_path}")
            svg = SVG.parse(str(measure_path))
            raw = count_paths_in_svg(svg)
            merged = raw
            hashes = [hashlib.sha256(s.d.encode()).hexdigest() for s in svg.shapes()]
        else:
            try:
                raw, merged, _, hashes = process_file_like_stage(
                    path, snap_grid=snap_grid
                )
            except Exception as e:
                per_glyph.append((path.name, 0, 0, False))
                blockers.append(f"picosvg failed on {path.name}: {e}")
                continue
        total_raw += raw
        total_merged += merged
        all_hashes.extend(hashes)
        is_flag = "waved-svg" in path.as_posix() or (
            path.parent == NOTO_WAVED_FLAG_SVG_DIR
        )
        per_glyph.append((path.name, raw, merged, is_flag))

    unique_outlines = len(set(all_hashes))
    # nanoemoji adds blank glyphs for tag chars etc.; rough upper bound
    estimated_glyphs = unique_outlines + len(paths) + 512

    return {
        "num_files": len(paths),
        "gradient_files": gradient_files,
        "total_raw_layers": total_raw,
        "total_merged_layers": total_merged,
        "unique_outline_hashes": unique_outlines,
        "estimated_glyph_ids": estimated_glyphs,
        "per_glyph": per_glyph,
        "blockers": blockers,
    }


def print_report(stats: Dict) -> None:
    print("COLRv0 budget report")
    print(f"  SVG inputs: {stats['num_files']}")
    print(f"  Files with gradients (source): {stats['gradient_files']}")
    print(f"  Raw picosvg layers (sum): {stats['total_raw_layers']} / {COLRV0_LIMIT}")
    print(f"  Merged layers (sum): {stats['total_merged_layers']} / {COLRV0_LIMIT}")
    print(
        f"  Unique outline hashes (estimate): {stats['unique_outline_hashes']} "
        f"(glyph estimate ~{stats['estimated_glyph_ids']} / {COLRV0_LIMIT})"
    )
    if stats["blockers"]:
        print(f"  Blockers / errors: {len(stats['blockers'])}")
        for line in stats["blockers"][:30]:
            print(f"    - {line}")
    worst = sorted(stats["per_glyph"], key=lambda x: x[2], reverse=True)[:20]
    print("  Top 20 glyphs by merged layer count:")
    for name, raw, merged, is_flag in worst:
        kind = "flag" if is_flag else "emoji"
        print(f"    {name}: raw={raw} merged={merged} ({kind})")
    flags = [x for x in stats["per_glyph"] if x[3]]
    faces = [x for x in stats["per_glyph"] if not x[3]]
    if flags:
        print(
            f"  Flags avg merged layers: {sum(x[2] for x in flags) / len(flags):.1f}"
        )
    if faces:
        print(
            f"  Emoji avg merged layers: {sum(x[2] for x in faces) / len(faces):.1f}"
        )


def over_limit(stats: Dict) -> bool:
    return (
        stats["total_merged_layers"] > COLRV0_LIMIT
        or stats["estimated_glyph_ids"] > COLRV0_LIMIT
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--staged",
        action="store_true",
        help="Measure colrv0/staged SVGs instead of re-running prep in memory",
    )
    parser.add_argument(
        "--require-under-limit",
        action="store_true",
        help="Exit with code 1 if merged layer or glyph estimates exceed 65535",
    )
    parser.add_argument("--snap-grid", type=float, default=None)
    args = parser.parse_args(argv)

    paths = all_colr_svg_paths()
    staged = Path("colrv0/staged") if args.staged else None
    stats = measure_sources(paths, staged_dir=staged, snap_grid=args.snap_grid)
    print_report(stats)
    if args.require_under_limit and over_limit(stats):
        print(
            "ERROR: COLRv0 limits exceeded. Adjust merging (e.g. --snap-grid) "
            "or fix blockers; not building font."
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())