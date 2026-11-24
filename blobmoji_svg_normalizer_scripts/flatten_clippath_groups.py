#!/usr/bin/env python3
"""Flatten <g> wrappers inside <clipPath> so picosvg can build COLRv1 fonts.

picosvg only accepts shape elements as direct clipPath children. Inkscape often
wraps clip geometry in groups (sometimes with transforms or nested clip-path).
"""
import argparse
import os
import sys

from lxml import etree

SVG_NS = "http://www.w3.org/2000/svg"
SVG = f"{{{SVG_NS}}}"
SHAPE_LOCAL_NAMES = frozenset(
    {"path", "circle", "ellipse", "line", "polygon", "polyline", "rect"}
)
GRADIENT_LOCAL_NAMES = frozenset({"linearGradient", "radialGradient"})


def local_name(tag: str) -> str:
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def is_shape(el: etree._Element) -> bool:
    return local_name(el.tag) in SHAPE_LOCAL_NAMES


def compose_transform(outer: str, inner: str) -> str:
    """Compose nested SVG transforms (outer group applied after inner)."""
    outer = (outer or "").strip()
    inner = (inner or "").strip()
    if not outer:
        return inner
    if not inner:
        return outer
    return f"{outer} {inner}"


def find_defs(root: etree._Element) -> etree._Element:
    for child in root:
        if local_name(child.tag) == "defs":
            return child
    defs = etree.Element(f"{SVG}defs")
    root.insert(0, defs)
    return defs


def is_id_referenced(root: etree._Element, elem_id: str) -> bool:
    needle = f"url(#{elem_id})"
    for el in root.iter():
        for value in el.attrib.values():
            if needle in value:
                return True
        style = el.get("style")
        if style and needle in style:
            return True
    return False


def clippath_needs_flatten(clip_el: etree._Element) -> bool:
    """True only when picosvg would choke on group/gradient content inside clipPath."""
    for el in clip_el.iter():
        if el is clip_el:
            continue
        tag = local_name(el.tag)
        if tag == "g" or tag in GRADIENT_LOCAL_NAMES:
            return True
    return False


def flatten_clippath(clip_el: etree._Element, root: etree._Element, defs_el: etree._Element) -> bool:
    if not clippath_needs_flatten(clip_el):
        return False

    shapes: list[etree._Element] = []
    promoted_clip_paths: list[str] = []

    def process(el: etree._Element, transform_prefix: str) -> None:
        tag = local_name(el.tag)
        if tag == "g":
            cp = el.get("clip-path")
            if cp:
                promoted_clip_paths.append(cp)
            next_prefix = compose_transform(transform_prefix, el.get("transform", ""))
            for child in list(el):
                process(child, next_prefix)
            return

        parent = el.getparent()
        if parent is None:
            return

        if is_shape(el):
            parent.remove(el)
            final_transform = compose_transform(transform_prefix, el.get("transform", ""))
            if final_transform:
                el.set("transform", final_transform)
            elif "transform" in el.attrib:
                del el.attrib["transform"]
            shapes.append(el)
            return

        if tag in GRADIENT_LOCAL_NAMES:
            grad_id = el.get("id")
            parent.remove(el)
            if grad_id and is_id_referenced(root, grad_id):
                defs_el.append(el)
            return

        parent.remove(el)

    for child in list(clip_el):
        process(child, "")

    unique_clips = {cp for cp in promoted_clip_paths if cp}
    if len(unique_clips) > 1:
        clip_id = clip_el.get("id", "?")
        raise ValueError(
            f"clipPath id={clip_id!r} has conflicting nested clip-path values: {unique_clips}"
        )

    if len(unique_clips) == 1:
        promoted = unique_clips.pop()
        existing = clip_el.get("clip-path")
        if existing and existing != promoted:
            clip_id = clip_el.get("id", "?")
            raise ValueError(
                f"clipPath id={clip_id!r} already has clip-path={existing!r}, "
                f"cannot promote {promoted!r}"
            )
        if not existing:
            clip_el.set("clip-path", promoted)

    if not shapes:
        clip_id = clip_el.get("id", "?")
        raise ValueError(
            f"clipPath id={clip_id!r}: flattening removed all geometry (unsupported content?)"
        )

    for child in list(clip_el):
        clip_el.remove(child)
    for shape in shapes:
        clip_el.append(shape)

    return True


def process_svg_file(path: str, dry_run: bool = False) -> bool:
    tree = etree.parse(path)
    root = tree.getroot()
    if local_name(root.tag) != "svg":
        return False

    defs_el = find_defs(root)
    changed = False
    for clip_el in root.iter(f"{SVG}clipPath"):
        if flatten_clippath(clip_el, root, defs_el):
            changed = True

    if changed and not dry_run:
        tree.write(
            path,
            pretty_print=True,
            xml_declaration=True,
            encoding="UTF-8",
        )
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--svg-dir",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "../svg"),
        help="Directory containing SVG files (default: ../svg)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report files that would change without writing",
    )
    args = parser.parse_args()
    svg_dir = os.path.abspath(args.svg_dir)
    if not os.path.isdir(svg_dir):
        print(f"Error: not a directory: {svg_dir}", file=sys.stderr)
        return 1

    n_changed = 0
    for name in sorted(os.listdir(svg_dir)):
        if not name.lower().endswith(".svg"):
            continue
        path = os.path.join(svg_dir, name)
        try:
            if process_svg_file(path, dry_run=args.dry_run):
                n_changed += 1
                label = "Would process" if args.dry_run else "Processed"
                print(f"{label}: {path}")
        except etree.XMLSyntaxError as exc:
            print(f"Error parsing {path}: {exc}", file=sys.stderr)
            return 1
        except ValueError as exc:
            print(f"Error in {path}: {exc}", file=sys.stderr)
            return 1

    print(f"Done. {n_changed} file(s) {'would be ' if args.dry_run else ''}updated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())