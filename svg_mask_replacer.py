#!/usr/bin/env python3
# Before using script: pip install svgelements
import os
import re
from pathlib import Path
import xml.etree.ElementTree as ET
import svgelements as sve

# Register SVG namespace to avoid "ns0" prefixes
ET.register_namespace("", "http://www.w3.org/2000/svg")
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

def replace_masks_in_svg(svg_file_path, output_folder):
    try:
        # Parse the SVG file
        tree = ET.parse(svg_file_path)
        root = tree.getroot()
        
        # Find all mask elements
        mask_elements = root.findall(".//{http://www.w3.org/2000/svg}mask")
        
        if not mask_elements:
            print(f"No masks found in {svg_file_path}")
            return False
        
        # Process each mask
        for mask in mask_elements:
            mask_id = mask.get('id', '')
            
            # Find all elements that reference this mask
            masked_elements = []
            for elem in root.iter():
                mask_url = elem.get('mask')
                if mask_url and f"url(#{mask_id})" in mask_url:
                    masked_elements.append(elem)
            
            # For each element using this mask, create a clipped version instead
            for masked_elem in masked_elements:
                # Create a clipPath element
                clip_id = f"clip_{mask_id}"
                clip_path = ET.SubElement(root, "{http://www.w3.org/2000/svg}clipPath")
                clip_path.set('id', clip_id)
                
                # Copy mask contents to clipPath
                for child in mask:
                    clip_child = ET.SubElement(clip_path, child.tag)
                    for attr_name, attr_value in child.attrib.items():
                        clip_child.set(attr_name, attr_value)
                
                # Replace mask with clipPath reference
                masked_elem.attrib.pop('mask')
                masked_elem.set('clip-path', f"url(#{clip_id})")
            
            # Remove the original mask
            parent = root.findall(f".//*[@id='{mask_id}']/..")
            if parent:
                parent[0].remove(mask)
        
        # Save the modified SVG
        output_file = os.path.join(output_folder, os.path.basename(svg_file_path))
        tree.write(output_file, encoding="utf-8", xml_declaration=True)
        print(f"Successfully processed {svg_file_path}")
        return True
    
    except Exception as e:
        print(f"Error processing {svg_file_path}: {e}")
        return False

def process_svg_folder(input_folder, output_folder):
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Get all SVG files
    svg_files = list(Path(input_folder).glob('*.svg'))
    
    if not svg_files:
        print(f"No SVG files found in {input_folder}")
        return
    
    processed = 0
    for svg_file in svg_files:
        if replace_masks_in_svg(svg_file, output_folder):
            processed += 1
    
    print(f"Processed {processed} out of {len(svg_files)} SVG files")

if __name__ == "__main__":
    # Define input and output folders
    input_folder = "svg"  # Change this to your SVG folder path
    output_folder = "svg"  # Change this to your desired output folder
    
    process_svg_folder(input_folder, output_folder)
