#!/usr/bin/env python3
"""Remove clip-path references to missing clipPath ids so picosvg can build COLRv1 fonts.

picosvg resolves every clip-path="url(#id)" to a <clipPath> element and fails if the
target is missing. Inkscape/Illustrator redesigns often leave SVGID_* refs after the
clipPath definition was deleted.
"""
import argparse
import os
import re
import sys

from lxml import etree

SVG_NS = "http://www.w3.org/2000/svg"
SVG = f"{{{SVG_NS}}}"
CLIP_URL_RE = re.compile(r"url\(#([^)]+)\)")


def local_name(tag: str) -> str:
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def collect_clippath_ids(root: etree._Element) -> set[str]:
    ids: set[str] = set()
    for el in root.iter():
        if local_name(el.tag) == "clipPath":
            eid = el.get("id")
            if eid:
                ids.add(eid)
    return ids


def clip_url_id(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    m = CLIP_URL_RE.fullmatch(value)
    if m:
        return m.group(1)
    return None


def strip_dangling_from_style(style: str, valid_ids: set[str]) -> tuple[str, bool]:
    changed = False
    parts: list[str] = []
    for raw in style.split(";"):
        chunk = raw.strip()
        if not chunk or ":" not in chunk:
            if chunk:
                parts.append(chunk)
            continue
        prop, val = chunk.split(":", 1)
        prop = prop.strip()
        val = val.strip()
        if prop == "clip-path":
            cid = clip_url_id(val)
            if cid is not None and cid not in valid_ids:
                changed = True
                continue
        parts.append(f"{prop}: {val}" if val else prop)
    new_style = "; ".join(parts)
    return new_style, changed


def strip_dangling_clip_refs(root: etree._Element) -> bool:
    valid_ids = collect_clippath_ids(root)
    changed = False
    for el in root.iter():
        for attr in list(el.attrib.keys()):
            if attr != "clip-path" and not attr.endswith("}clip-path"):
                continue
            cid = clip_url_id(el.get(attr))
            if cid is not None and cid not in valid_ids:
                del el.attrib[attr]
                changed = True
        style = el.get("style")
        if style:
            new_style, style_changed = strip_dangling_from_style(style, valid_ids)
            if style_changed:
                changed = True
                if new_style:
                    el.set("style", new_style)
                elif "style" in el.attrib:
                    del el.attrib["style"]
    return changed


def process_svg_file(path: str, dry_run: bool = False) -> bool:
    tree = etree.parse(path)
    root = tree.getroot()
    if local_name(root.tag) != "svg":
        return False

    changed = strip_dangling_clip_refs(root)
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

    print(f"Done. {n_changed} file(s) {'would be ' if args.dry_run else ''}updated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())