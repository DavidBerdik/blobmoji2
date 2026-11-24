#!/usr/bin/env python3
"""Remove SVG 1.1 <font> trees so picosvg can build COLRv1 fonts.

picosvg only allows path/g under the root (plus defs/gradients). Inkscape often
leaves <font>, <font-face>, and <glyph> elements after --export-text-to-path.
"""
import argparse
import os
import sys

from lxml import etree

SVG_NS = "http://www.w3.org/2000/svg"
SVG = f"{{{SVG_NS}}}"
FONT_LOCAL_NAMES = frozenset(
    {"font", "font-face", "glyph", "missing-glyph", "hkern", "vkern"}
)


def local_name(tag: str) -> str:
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def strip_font_elements(root: etree._Element) -> bool:
    """Remove <font> and stray font-related elements not under defs."""
    changed = False
    for el in list(root.iter()):
        if el is root:
            continue
        name = local_name(el.tag)
        if name == "font":
            parent = el.getparent()
            if parent is not None:
                parent.remove(el)
                changed = True
        elif name in FONT_LOCAL_NAMES:
            parent = el.getparent()
            if parent is not None and local_name(parent.tag) != "font":
                parent.remove(el)
                changed = True
    return changed


def process_svg_file(path: str, dry_run: bool = False) -> bool:
    tree = etree.parse(path)
    root = tree.getroot()
    if local_name(root.tag) != "svg":
        return False

    changed = strip_font_elements(root)
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