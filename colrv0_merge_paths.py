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

"""Merge same-paint paths in picosvg SVG trees to reduce COLRv0 layer count."""

from __future__ import annotations

import logging
import re
from typing import List, Optional, Sequence, Tuple

from picosvg.svg import SVG
from picosvg.svg_pathops import intersection as path_intersection
from picosvg.svg_pathops import path_area
from picosvg.svg_pathops import remove_overlaps
from picosvg.svg_pathops import union as path_union
from picosvg.svg_types import SVGPath

log = logging.getLogger(__name__)

XLINK_HREF_RE = re.compile(r"url\(#([^)]+)\)")


def paint_key(shape: SVGPath) -> str:
    """Identity for COLRv0 layer paint (fill + opacity + rule)."""
    fill = (shape.fill or "none").strip().lower()
    opacity = shape.opacity if shape.opacity is not None else 1.0
    fill_opacity = shape.fill_opacity if shape.fill_opacity is not None else 1.0
    rule = (shape.fill_rule or "nonzero").strip().lower()
    return f"{fill}|{opacity:.6f}|{fill_opacity:.6f}|{rule}"


def _bbox(shape: SVGPath) -> Optional[Tuple[float, float, float, float]]:
    box = shape.bounding_box()
    if box is None:
        return None
    return (box.x, box.y, box.x + box.w, box.y + box.h)


def _bboxes_overlap(a: Tuple[float, float, float, float], b: Tuple[float, float, float, float]) -> bool:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    return ax0 < bx1 and ax1 > bx0 and ay0 < by1 and ay1 > by0


def _shapes_overlap(a: SVGPath, b: SVGPath, *, bbox_only: bool = False) -> bool:
    if bbox_only:
        ba, bb = _bbox(a), _bbox(b)
        if ba is None or bb is None:
            return True
        return _bboxes_overlap(ba, bb)
    return _paths_intersect(a, b)


def _paths_intersect(a: SVGPath, b: SVGPath) -> bool:
    try:
        a, b = _prepare_for_pathops(a), _prepare_for_pathops(b)
        rules = [a.fill_rule or "nonzero", b.fill_rule or "nonzero"]
        cmds = list(path_intersection([tuple(a), tuple(b)], rules))
        return bool(cmds)
    except Exception:
        return True


def _fill_rules(shapes: Sequence[SVGPath]) -> List[str]:
    return [(s.fill_rule or "nonzero") for s in shapes]


def _prepare_for_pathops(shape: SVGPath) -> SVGPath:
    """Convert arcs/shorthand curves so skia-pathops can union paths."""
    return (
        shape.explicit_lines(inplace=False)
        .absolute(inplace=False)
        .arcs_to_cubics(inplace=False)
    )


def _union_shapes_chunked(shapes: Sequence[SVGPath], chunk: int = 25) -> List[SVGPath]:
    if len(shapes) <= chunk:
        return _union_shapes(shapes)
    parts: List[SVGPath] = []
    for i in range(0, len(shapes), chunk):
        parts.extend(_union_shapes(shapes[i : i + chunk]))
    while len(parts) > 1:
        nxt: List[SVGPath] = []
        for i in range(0, len(parts), chunk):
            nxt.extend(_union_shapes(parts[i : i + chunk]))
        if len(nxt) >= len(parts):
            break
        parts = nxt
    return parts


def _overlap_components(run: Sequence[SVGPath]) -> List[List[SVGPath]]:
    if not run:
        return []
    components: List[List[SVGPath]] = [[run[0]]]
    for shape in run[1:]:
        box = _bbox(shape)
        prev = components[-1]
        if box and any(
            _bboxes_overlap(box, b) for s in prev if (b := _bbox(s)) is not None
        ):
            prev.append(shape)
        else:
            components.append([shape])
    return components


def _flush_consecutive_run(run: Sequence[SVGPath]) -> List[SVGPath]:
    """Union same-paint runs; keep Illustrator stacks that would merge incorrectly."""
    out: List[SVGPath] = []
    for comp in _overlap_components(run):
        if len(comp) <= 2:
            out.extend(_union_shapes(comp))
            continue
        trial = _union_shapes(comp)
        stroke_pairs = any(
            is_stroke_outline_pair(comp[i], comp[i + 1]) for i in range(len(comp) - 1)
        )
        if len(trial) == 1 and stroke_pairs:
            out.extend(comp)
            continue
        i = 0
        while i < len(comp):
            if i + 1 < len(comp) and is_stroke_outline_pair(comp[i], comp[i + 1]):
                out.append(comp[i])
                out.append(comp[i + 1])
                i += 2
                continue
            j = i + 1
            while j < len(comp) and (
                j + 1 >= len(comp)
                or not is_stroke_outline_pair(comp[j], comp[j + 1])
            ):
                j += 1
            out.extend(_union_shapes(comp[i:j]))
            i = j
    return out


def _union_shapes(
    shapes: Sequence[SVGPath], *, reject_long_merge: bool = False
) -> List[SVGPath]:
    """Union shapes sharing paint; on failure return the inputs unchanged."""
    if len(shapes) == 1:
        return [shapes[0]]
    try:
        prepared = [_prepare_for_pathops(s) for s in shapes]
        rules = _fill_rules(prepared)
        cmd_seqs = [tuple(s) for s in prepared]
        # Opaque COLR layers composite as coverage union; each path keeps its fill rule.
        layered = list(path_union(cmd_seqs, rules))
        if not layered:
            return list(shapes)
        simplified = list(remove_overlaps(layered, "nonzero"))
        if not simplified:
            return list(shapes)
        a_layered = path_area(layered, "nonzero")
        a_simplified = path_area(simplified, "nonzero")
        if abs(a_layered - a_simplified) > 0.5:
            log.debug(
                "union simplify area mismatch %.2f vs %.2f; keeping %s paths",
                a_layered,
                a_simplified,
                len(shapes),
            )
            return list(shapes)
        merged = SVGPath.from_commands(simplified)
        if not merged.d or not merged.d.strip():
            return list(shapes)
        merged.fill = shapes[0].fill
        merged.fill_opacity = shapes[0].fill_opacity
        merged.opacity = shapes[0].opacity
        merged.fill_rule = "nonzero"
        return [merged]
    except Exception as e:
        log.debug("union failed (%s paths): %s", len(shapes), e)
        return list(shapes)


def _shape_area(shape: SVGPath) -> float:
    try:
        prepared = _prepare_for_pathops(shape)
        return path_area(tuple(prepared), shape.fill_rule or "nonzero")
    except Exception:
        return 0.0


def visible_ink_area(shapes: Sequence[SVGPath]) -> float:
    """Occlusion-aware sum of visible opaque fill area in paint order."""
    if not shapes:
        return 0.0
    acc_cmds: Optional[Tuple[tuple, ...]] = None
    acc_rule = "nonzero"
    total = 0.0
    for shape in shapes:
        try:
            prepared = _prepare_for_pathops(shape)
            rule = shape.fill_rule or "nonzero"
            cmds = tuple(prepared)
            a_shape = path_area(cmds, rule)
            if acc_cmds is None:
                total += a_shape
            else:
                inter = list(path_intersection([cmds, acc_cmds], [rule, acc_rule]))
                a_inter = path_area(inter, "nonzero") if inter else 0.0
                total += max(0.0, a_shape - a_inter)
            united = list(path_union([cmds, acc_cmds] if acc_cmds else [cmds], [rule, acc_rule] if acc_cmds else [rule]))
            if united:
                acc_cmds = tuple(united)
                acc_rule = "nonzero"
        except Exception:
            total += _shape_area(shape)
    return total


def _bbox_contains(
    outer: Tuple[float, float, float, float],
    inner: Tuple[float, float, float, float],
) -> bool:
    ox0, oy0, ox1, oy1 = outer
    ix0, iy0, ix1, iy1 = inner
    return ox0 <= ix0 and oy0 <= iy0 and ox1 >= ix1 and oy1 >= iy1


def is_nested_coverage_pair(a: SVGPath, b: SVGPath) -> bool:
    """Same paint: b is a larger covering layer over a (e.g. flashlight lens over body)."""
    if paint_key(a) != paint_key(b):
        return False
    ba, bb = _bbox(a), _bbox(b)
    if not ba or not bb or not _bboxes_overlap(ba, bb):
        return False
    if not _bbox_contains(bb, ba):
        return False
    aa, ab = _shape_area(a), _shape_area(b)
    la, lb = len(a.d or ""), len(b.d or "")
    if ab <= aa * 1.25:
        return False
    if lb < la * 1.5:
        return False
    return True


def is_stroke_outline_pair(a: SVGPath, b: SVGPath) -> bool:
    """Illustrator-style same-color fill immediately followed by an outline trace."""
    if paint_key(a) != paint_key(b):
        return False
    ba, bb = _bbox(a), _bbox(b)
    if not ba or not bb or not _bboxes_overlap(ba, bb):
        return False
    aa, ab = _shape_area(a), _shape_area(b)
    la, lb = len(a.d or ""), len(b.d or "")
    if _bbox_contains(ba, bb) and ab > aa * 1.05 and lb > la * 1.15:
        return True
    if _bbox_contains(bb, ba) and aa > ab * 1.05 and la > lb * 1.15:
        return True
    if _bbox_contains(bb, ba) and lb > la * 1.35 and ab < aa * 0.32:
        return True
    return False


def merge_consecutive_same_paint(shapes: Sequence[SVGPath]) -> List[SVGPath]:
    """Rung A: union consecutive paths with the same paint."""
    if not shapes:
        return []
    out: List[SVGPath] = []
    run: List[SVGPath] = [shapes[0]]
    key = paint_key(shapes[0])
    for shape in shapes[1:]:
        if paint_key(shape) == key:
            if run and is_nested_coverage_pair(run[-1], shape):
                out.extend(_flush_consecutive_run(run))
                out.append(shape)
                run = [shape]
            else:
                run.append(shape)
        else:
            out.extend(_flush_consecutive_run(run))
            run = [shape]
            key = paint_key(shape)
    out.extend(_flush_consecutive_run(run))
    return out


def _normalize_shape_for_colrv0(shape: SVGPath) -> SVGPath:
    """Simplify each layer outline for predictable COLRv0 rasterization."""
    try:
        prepared = _prepare_for_pathops(shape)
        rule = shape.fill_rule or "nonzero"
        simplified = list(remove_overlaps(tuple(prepared), rule))
        if not simplified:
            return shape
        a0 = path_area(tuple(prepared), rule)
        a1 = path_area(simplified, "nonzero")
        if abs(a0 - a1) > 0.5:
            return shape
        norm = SVGPath.from_commands(simplified)
        if not norm.d or not norm.d.strip():
            return shape
        norm.fill = shape.fill
        norm.fill_opacity = shape.fill_opacity
        norm.opacity = shape.opacity
        norm.fill_rule = "nonzero"
        return norm
    except Exception as e:
        log.debug("normalize shape failed: %s", e)
        return shape


def _can_merge_across(
    indices: List[int],
    shapes: Sequence[SVGPath],
    between: Sequence[int],
) -> bool:
    """True if merging shapes at indices does not change compositing vs between paths."""
    targets = [shapes[i] for i in indices]
    target_boxes = [_bbox(t) for t in targets]
    for j in between:
        mid = shapes[j]
        mid_box = _bbox(mid)
        if mid_box is None:
            return False
        for t, tbox in zip(targets, target_boxes):
            if tbox is None:
                return False
            if not _bboxes_overlap(mid_box, tbox):
                continue
            if _paths_intersect(mid, t):
                return False
    return True


def _subset_must_stay_separate(shapes: Sequence[SVGPath]) -> bool:
    for i in range(len(shapes)):
        for j in range(i + 1, len(shapes)):
            if is_stroke_outline_pair(shapes[i], shapes[j]) or is_nested_coverage_pair(
                shapes[i], shapes[j]
            ):
                return True
            if is_stroke_outline_pair(shapes[j], shapes[i]) or is_nested_coverage_pair(
                shapes[j], shapes[i]
            ):
                return True
    return False


def merge_non_consecutive_same_paint(shapes: Sequence[SVGPath]) -> List[SVGPath]:
    """Rung B: merge all same-paint paths in a span when in-between paths do not overlap."""
    remaining = list(shapes)
    changed = True
    while changed:
        changed = False
        by_paint: dict[str, List[int]] = {}
        for i, s in enumerate(remaining):
            by_paint.setdefault(paint_key(s), []).append(i)
        for idxs in by_paint.values():
            if len(idxs) < 2:
                continue
            lo, hi = min(idxs), max(idxs)
            between = [j for j in range(lo + 1, hi) if j not in idxs]
            if not _can_merge_across(idxs, remaining, between):
                continue
            subset = [remaining[i] for i in idxs]
            if _subset_must_stay_separate(subset):
                continue
            before_len = len(remaining)
            merged_list = _union_shapes(subset)
            if len(merged_list) >= len(idxs):
                continue
            remaining = (
                remaining[:lo]
                + merged_list
                + [remaining[j] for j in range(lo + 1, len(remaining)) if j not in idxs]
            )
            if len(remaining) < before_len:
                changed = True
                break
    return remaining


def snap_path_coordinates(shapes: Sequence[SVGPath], grid: float = 0.25) -> List[SVGPath]:
    """Rung C: snap path coordinates to a fine grid in user units."""
    if grid <= 0:
        return list(shapes)
    out: List[SVGPath] = []
    for shape in shapes:
        snapped = SVGPath(d=shape.d, fill=shape.fill)
        snapped.fill_opacity = shape.fill_opacity
        snapped.opacity = shape.opacity
        snapped.fill_rule = shape.fill_rule
        # Round coordinates in path d string (picosvg uses absolute coords)
        def round_match(m):
            return str(round(float(m.group(0)) / grid) * grid)

        snapped.d = re.sub(r"-?\d+\.?\d*", round_match, shape.d)
        out.append(snapped)
    return out


def merge_waved_flag_by_paint(shapes: Sequence[SVGPath]) -> List[SVGPath]:
    """Union all paths per paint in z-order of first appearance (for dense waved flags)."""
    paint_order: List[str] = []
    groups: dict[str, List[SVGPath]] = {}
    for shape in shapes:
        key = paint_key(shape)
        if key not in groups:
            paint_order.append(key)
            groups[key] = []
        groups[key].append(shape)
    result: List[SVGPath] = []
    for key in paint_order:
        result.extend(_union_shapes_chunked(groups[key]))
    return result


def merge_disjoint_same_paint(
    shapes: Sequence[SVGPath], *, bbox_only: bool = False
) -> List[SVGPath]:
    """Group same-paint paths that do not overlap each other, then union each group."""
    result: List[SVGPath] = []
    i = 0
    while i < len(shapes):
        key = paint_key(shapes[i])
        j = i + 1
        while j < len(shapes) and paint_key(shapes[j]) == key:
            j += 1
        run = list(shapes[i:j])
        if len(run) == 1:
            result.append(run[0])
        else:
            clusters: List[List[SVGPath]] = []
            for shape in run:
                placed = False
                for cluster in clusters:
                    if all(
                        not _shapes_overlap(shape, other, bbox_only=bbox_only)
                        for other in cluster
                    ):
                        cluster.append(shape)
                        placed = True
                        break
                if not placed:
                    clusters.append([shape])
            for cluster in clusters:
                result.extend(_union_shapes(cluster))
        i = j
    return result


def merge_shapes_for_colrv0(
    shapes: Sequence[SVGPath],
    *,
    non_consecutive: bool = True,
    snap_grid: Optional[float] = None,
    disjoint_same_paint: bool = False,
    disjoint_bbox_only: bool = False,
    waved_flag_merge: bool = False,
) -> List[SVGPath]:
    current = list(shapes)
    if snap_grid is not None:
        current = snap_path_coordinates(current, snap_grid)
    current = merge_consecutive_same_paint(current)
    if waved_flag_merge:
        current = merge_waved_flag_by_paint(current)
    elif disjoint_same_paint:
        current = merge_disjoint_same_paint(current, bbox_only=disjoint_bbox_only)
    if non_consecutive:
        current = merge_non_consecutive_same_paint(current)
    return [_normalize_shape_for_colrv0(s) for s in current]


def clip_and_drop_empty(svg: SVG) -> SVG:
    """Clip to the viewBox and drop paths nanoemoji cannot turn into COLR layers."""
    try:
        svg.clip_to_viewbox(inplace=True)
    except Exception as e:
        log.warning("clip_to_viewbox failed: %s", e)
    kept = []
    for shape in svg.shapes():
        d = (shape.as_path().d or "").strip()
        if d.startswith("M"):
            kept.append(shape)
    if len(kept) != len(tuple(svg.shapes())):
        return rebuild_svg_with_shapes(svg, kept)
    return svg


def count_paths_in_svg(svg: SVG) -> int:
    return len(tuple(svg.shapes()))


def rebuild_svg_with_shapes(svg: SVG, shapes: Sequence[SVGPath]) -> SVG:
    """Return a new picosvg SVG containing only the given paths."""
    from lxml import etree

    vb = svg.view_box()
    ns = "http://www.w3.org/2000/svg"
    root = etree.Element(f"{{{ns}}}svg", nsmap={None: ns})
    root.set("viewBox", f"{vb.x} {vb.y} {vb.w} {vb.h}")
    root.append(etree.Element(f"{{{ns}}}defs"))
    for shape in shapes:
        d = (shape.d or "").strip()
        if not d or d[0] not in "MmZzLlHhVvCcSsQqTtAa":
            continue
        path = etree.SubElement(root, f"{{{ns}}}path")
        path.set("d", d)
        if shape.fill and shape.fill != "none":
            path.set("fill", shape.fill)
        if shape.fill_opacity is not None and shape.fill_opacity != 1.0:
            path.set("fill-opacity", str(shape.fill_opacity))
        if shape.opacity is not None and shape.opacity != 1.0:
            path.set("opacity", str(shape.opacity))
        if shape.fill_rule:
            path.set("fill-rule", shape.fill_rule)
    return SVG(root)


def process_picosvg_tree(
    svg: SVG,
    *,
    non_consecutive: bool = True,
    snap_grid: Optional[float] = None,
) -> SVG:
    shapes = tuple(svg.shapes())
    merged = merge_shapes_for_colrv0(
        shapes, non_consecutive=non_consecutive, snap_grid=snap_grid
    )
    return rebuild_svg_with_shapes(svg, merged)