#!/usr/bin/env python3
import os
import re
from pathlib import Path
import xml.etree.ElementTree as ET

# Register SVG namespace to avoid "ns0" prefixes
ET.register_namespace("", "http://www.w3.org/2000/svg")
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

def remove_px_suffix(svg_file_path, output_folder):
    try:
        # Read the SVG file as text
        with open(svg_file_path, 'r', encoding='utf-8') as file:
            svg_content = file.read()
        
        # Use regex to find and remove px suffixes from numeric values
        # This pattern looks for numbers followed by 'px' in attribute values
        pattern = r'(\d+(\.\d+)?)px'
        modified_content = re.sub(pattern, r'\1', svg_content)
        
        # Save the modified SVG
        output_file = os.path.join(output_folder, os.path.basename(svg_file_path))
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(modified_content)
        
        # Check if we made any changes
        if svg_content != modified_content:
            print(f"Successfully removed px suffixes from {svg_file_path}")
            return True
        else:
            print(f"No px suffixes found in {svg_file_path}")
            return False
            
    except Exception as e:
        print(f"Error processing {svg_file_path}: {e}")
        return False

def process_svg_folder(input_folder, output_folder, dry_run=False):
    # Create output folder if it doesn't exist and this isn't a dry run
    if not dry_run:
        os.makedirs(output_folder, exist_ok=True)
    
    # Get all SVG files
    svg_files = list(Path(input_folder).glob('*.svg'))
    
    if not svg_files:
        print(f"No SVG files found in {input_folder}")
        return
    
    processed = 0
    modified = 0
    
    for svg_file in svg_files:
        if dry_run:
            # Just check if the file contains px suffixes
            with open(svg_file, 'r', encoding='utf-8') as file:
                content = file.read()
            if re.search(r'(\d+(\.\d+)?)px', content):
                print(f"Would modify: {svg_file}")
                modified += 1
            processed += 1
        else:
            # Actually process the file
            if remove_px_suffix(svg_file, output_folder):
                modified += 1
            processed += 1
    
    action_verb = "Would modify" if dry_run else "Modified"
    print(f"Processed {processed} SVG files. {action_verb} {modified} files.")

if __name__ == "__main__":
    # Define input and output folders
    input_folder = "svg"  # Change this to your SVG folder path
    output_folder = "svg"  # Change this to your desired output folder
    
    # Set to True to check which files would be modified without changing anything
    dry_run = False
    
    process_svg_folder(input_folder, output_folder, dry_run)
