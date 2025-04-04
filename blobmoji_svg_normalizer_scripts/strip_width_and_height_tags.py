#!/usr/bin/env python3
import os
from lxml import etree

# Define the folder containing SVG files
svg_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../svg')

# Iterate over all files in the folder
for filename in os.listdir(svg_folder):
    if filename.endswith(".svg"):
        file_path = os.path.join(svg_folder, filename)
        
        # Parse the SVG file
        try:
            tree = etree.parse(file_path)
            root = tree.getroot()
            
            # Check if the root tag is <svg>
            if root.tag == '{http://www.w3.org/2000/svg}svg':
                # Remove width and height attributes if they exist
                root.attrib.pop("width", None)
                root.attrib.pop("height", None)
                
                # Write the changes back to the file without namespaces
                with open(file_path, 'wb') as f:
                    f.write(etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8'))
                print(f"Processed: {filename}")
            else:
                print(f"Skipped (not an SVG root): {filename}")
        except etree.XMLSyntaxError:
            print(f"Error parsing file: {filename}")
