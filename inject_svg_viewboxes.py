#!/usr/bin/env python3
import os
import xml.etree.ElementTree as ET

def add_viewbox_if_missing(svg_path):
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()

        # SVGs usually use this namespace
        if '}' in root.tag:
            ns = root.tag.split('}')[0].strip('{')
            ET.register_namespace('', ns)

        # Check if viewBox exists
        if 'viewBox' not in root.attrib:
            width = root.attrib.get('width')
            height = root.attrib.get('height')

            # Strip "px" if present and convert to float
            try:
                w = float(width.replace('px', '')) if width else None
                h = float(height.replace('px', '')) if height else None
            except ValueError:
                print(f"⚠️  Invalid width/height in {svg_path}")
                return

            if w is not None and h is not None:
                viewbox_value = f"0 0 {int(w)} {int(h)}"
                root.set('viewBox', viewbox_value)
                tree.write(svg_path, encoding='utf-8', xml_declaration=True)
                print(f"✅ Added viewBox to: {os.path.basename(svg_path)}")
            else:
                print(f"⚠️  No width/height to infer viewBox in {svg_path}")
        else:
            print(f"✔️  viewBox already present in: {os.path.basename(svg_path)}")

    except ET.ParseError:
        print(f"❌ Failed to parse: {svg_path}")

def process_folder(folder_path):
    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.svg'):
            file_path = os.path.join(folder_path, filename)
            add_viewbox_if_missing(file_path)

if __name__ == '__main__':
    folder = input("Enter the path to your SVG folder: ").strip()
    if os.path.isdir(folder):
        process_folder(folder)
    else:
        print("❌ Invalid folder path.")
