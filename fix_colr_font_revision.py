"""Set COLRv1 fontRevision from CBDT.

Used for bugfix, should fix to set properly on build instead.
"""

from fontTools import ttLib
from pathlib import Path
import sys


NAME_ID_VERSION = 5


def name(font, name_id):
    return ",".join(n.toUnicode() for n in font["name"].names if n.isUnicode() and n.nameID == name_id)


def _cbdt_pair_path(colr_font_file: Path) -> Path:
    stem = colr_font_file.stem
    for prefix in ("Noto-COLRv1", "Noto-COLRv0"):
        if stem.startswith(prefix):
            stem = stem.replace(prefix, "NotoColorEmoji", 1)
            break
    return colr_font_file.with_name(stem + colr_font_file.suffix)


def main():
    colr_font_files = sorted(
        p
        for p in (Path(__file__).parent / "fonts").iterdir()
        if p.name.startswith("Noto-COLRv1") or p.name.startswith("Noto-COLRv0")
    )

    for colr_font_file in colr_font_files:
        cbdt_font_file = _cbdt_pair_path(colr_font_file)

        colr_font = ttLib.TTFont(colr_font_file)
        cbdt_font = ttLib.TTFont(cbdt_font_file)

        assert "CBDT" in cbdt_font
        assert "COLR" in colr_font

        colr_font["head"].fontRevision = cbdt_font["head"].fontRevision

        colr_font.save(colr_font_file)


if __name__ == '__main__':
  main()
