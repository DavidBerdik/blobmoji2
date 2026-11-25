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

"""Prepare raw SVG files for COLRv0 (gradient flatten, strip unused images)."""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from lxml import etree

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
NSMAP = {None: SVG_NS, "xlink": XLINK_NS}
HREF_ATTRS = ("href", f"{{{XLINK_NS}}}href")


def local_name(tag: str) -> str:
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def _parse_color(value: str) -> Tuple[float, float, float, float]:
    value = value.strip()
    if not value or value.lower() == "none":
        return (0.0, 0.0, 0.0, 0.0)
    if value.startswith("#"):
        h = value[1:]
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        if len(h) == 6:
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            return (r / 255.0, g / 255.0, b / 255.0, 1.0)
        if len(h) == 8:
            r, g, b, a = (
                int(h[0:2], 16),
                int(h[2:4], 16),
                int(h[4:6], 16),
                int(h[6:8], 16),
            )
            return (r / 255.0, g / 255.0, b / 255.0, a / 255.0)
    m = re.match(
        r"rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)(?:\s*,\s*([\d.]+))?\s*\)",
        value,
        re.I,
    )
    if m:
        r, g, b = float(m.group(1)) / 255.0, float(m.group(2)) / 255.0, float(m.group(3)) / 255.0
        a = float(m.group(4)) if m.group(4) is not None else 1.0
        if r > 1 or g > 1 or b > 1:
            r, g, b = r * (255 if r > 1 else 1), g * (255 if g > 1 else 1), b * (255 if b > 1 else 1)
            r, g, b = r / 255.0, g / 255.0, b / 255.0
        return (r, g, b, a)
    return (0.5, 0.5, 0.5, 1.0)


def _color_to_hex(rgba: Tuple[float, float, float, float]) -> str:
    r, g, b, a = rgba
    if a < 0.999:
        return "#{:02x}{:02x}{:02x}{:02x}".format(
            int(round(r * 255)),
            int(round(g * 255)),
            int(round(b * 255)),
            int(round(a * 255)),
        )
    return "#{:02x}{:02x}{:02x}".format(
        int(round(r * 255)), int(round(g * 255)), int(round(b * 255))
    )


def _stop_color(stop: etree._Element) -> Tuple[float, float, float, float]:
    color = stop.get("stop-color")
    opacity = stop.get("stop-opacity", "1")
    style = stop.get("style") or ""
    for part in style.split(";"):
        part = part.strip()
        if part.startswith("stop-color:"):
            color = part.split(":", 1)[1].strip()
        elif part.startswith("stop-opacity:"):
            opacity = part.split(":", 1)[1].strip()
    rgba = _parse_color(color or "#808080")
    try:
        a = float(opacity)
    except (TypeError, ValueError):
        a = 1.0
    return (rgba[0], rgba[1], rgba[2], rgba[3] * a)


def _gradient_stops(grad: etree._Element) -> List[Tuple[float, Tuple[float, float, float, float]]]:
    stops = []
    for child in grad:
        if local_name(child.tag) != "stop":
            continue
        offset = child.get("offset", "0")
        if offset.endswith("%"):
            off = float(offset[:-1]) / 100.0
        else:
            off = float(offset)
        stops.append((off, _stop_color(child)))
    stops.sort(key=lambda x: x[0])
    return stops


def _resolve_gradient(grad_el: etree._Element, by_id: Dict[str, etree._Element]) -> etree._Element:
    for attr in HREF_ATTRS:
        ref = grad_el.get(attr)
        if ref and ref.startswith("#"):
            ref_id = ref[1:]
            if ref_id in by_id:
                template = by_id[ref_id]
                if template is not grad_el:
                    _resolve_gradient(template, by_id)
                if not list(grad_el):
                    for stop in template:
                        if local_name(stop.tag) == "stop":
                            grad_el.append(etree.fromstring(etree.tostring(stop)))
    return grad_el


def _color_at_offset(stops: List[Tuple[float, Tuple[float, float, float, float]]], t: float = 0.5):
    if not stops:
        return "#808080"
    if len(stops) == 1:
        return _color_to_hex(stops[0][1])
    if all(s[1] == stops[0][1] for s in stops):
        return _color_to_hex(stops[0][1])
    for i in range(len(stops) - 1):
        o0, c0 = stops[i]
        o1, c1 = stops[i + 1]
        if o0 <= t <= o1:
            if o1 == o0:
                return _color_to_hex(c0)
            f = (t - o0) / (o1 - o0)
            mix = tuple(c0[j] + f * (c1[j] - c0[j]) for j in range(4))
            return _color_to_hex(mix)
    return _color_to_hex(stops[-1][1])


def flatten_gradients(root: etree._Element) -> None:
    """Replace gradient paints with solid fills at offset 0.5 (in-place)."""
    by_id: Dict[str, etree._Element] = {}
    for el in root.iter():
        el_id = el.get("id")
        if el_id:
            by_id[el_id] = el
    gradients = [
        el
        for el in root.iter()
        if local_name(el.tag) in ("linearGradient", "radialGradient")
    ]
    for grad in gradients:
        _resolve_gradient(grad, by_id)
    solid_by_id = {}
    for grad in gradients:
        gid = grad.get("id")
        if gid:
            solid_by_id[gid] = _color_at_offset(_gradient_stops(grad))

    url_re = re.compile(r"url\(#([^)]+)\)")

    def replace_paint(value: Optional[str]) -> Optional[str]:
        if not value:
            return value
        m = url_re.match(value.strip())
        if m and m.group(1) in solid_by_id:
            return solid_by_id[m.group(1)]
        return value

    for el in root.iter():
        for attr in ("fill", "stroke"):
            v = el.get(attr)
            nv = replace_paint(v)
            if nv != v:
                el.set(attr, nv)
        style = el.get("style")
        if style and "url(#" in style:
            parts = []
            for part in style.split(";"):
                part = part.strip()
                if not part:
                    continue
                if ":" in part:
                    key, val = part.split(":", 1)
                    val = replace_paint(val.strip()) or val.strip()
                    parts.append(f"{key.strip()}:{val}")
                else:
                    parts.append(part)
            el.set("style", ";".join(parts))

    for grad in gradients:
        parent = grad.getparent()
        if parent is not None:
            parent.remove(grad)


def strip_unused_images(root: etree._Element) -> None:
    """Remove unreferenced <image> elements (picosvg does not support raster images)."""
    referenced = set()
    for el in root.iter():
        for attr in ("href", f"{{{XLINK_NS}}}href", "clip-path", "fill", "mask", "filter"):
            val = el.get(attr) or ""
            if "url(#" in val:
                for m in re.finditer(r"url\(#([^)]+)\)", val):
                    referenced.add(m.group(1))
        val = el.get("style") or ""
        if "url(#" in val:
            for m in re.finditer(r"url\(#([^)]+)\)", val):
                referenced.add(m.group(1))

    for img in list(root.iter(f"{{{SVG_NS}}}image")):
        img_id = img.get("id")
        if img_id and img_id not in referenced:
            parent = img.getparent()
            if parent is not None:
                parent.remove(img)


def strip_inkscape_metadata(root: etree._Element) -> None:
    for tag in ("namedview", "metadata"):
        for el in list(root.iter()):
            if local_name(el.tag) == tag:
                parent = el.getparent()
                if parent is not None:
                    parent.remove(el)


def prepare_svg_root(tree: etree._Element) -> etree._Element:
    root = tree if local_name(tree.tag) == "svg" else tree.find(f".//{{{SVG_NS}}}svg")
    if root is None:
        raise ValueError("No svg root")
    strip_inkscape_metadata(root)
    strip_unused_images(root)
    flatten_gradients(root)
    return root


def load_and_prepare_svg(path: str) -> etree._Element:
    parser = etree.XMLParser(remove_comments=True)
    tree = etree.parse(path, parser)
    return prepare_svg_root(tree.getroot())