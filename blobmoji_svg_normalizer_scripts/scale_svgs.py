#!/usr/bin/env python3
import os
import xml.etree.ElementTree as ET

# Define the target viewBox
TARGET_VIEWBOX = "0 0 128 128"
TARGET_WIDTH = 128
TARGET_HEIGHT = 128

# Folder containing SVG files
SVG_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../svg')

# SVG namespace
SVG_NAMESPACE = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NAMESPACE)

# Iterate over all SVG files in the folder
for filename in os.listdir(SVG_FOLDER):
    if filename.endswith(".svg"):
        filepath = os.path.join(SVG_FOLDER, filename)
        
        # Parse the SVG file
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            continue
        
        # Get the current viewBox
        current_viewbox = root.attrib.get("viewBox")
        
        # Check if the viewBox matches the target
        if current_viewbox == TARGET_VIEWBOX:
            print(f"{filename}: ViewBox is already correct.")
            continue
        
        print(f"{filename}: Modifying viewBox from {current_viewbox} to {TARGET_VIEWBOX}.")
        
        # Parse the current viewBox values
        if current_viewbox:
            try:
                x, y, width, height = map(float, current_viewbox.split())
            except ValueError:
                print(f"{filename}: Invalid viewBox format, skipping.")
                continue
        else:
            # If no viewBox is found, use the width and height attributes
            width = float(root.attrib.get("width", TARGET_WIDTH))
            height = float(root.attrib.get("height", TARGET_HEIGHT))
            x, y = 0, 0
        
        # Create a new <g> element to group all contents
        group = ET.Element(f"{{{SVG_NAMESPACE}}}g")
        
        # Move all child elements of the root into the group
        for child in list(root):
            group.append(child)
            root.remove(child)
        
        # Add the group back to the root
        root.append(group)
        
        # Calculate scaling factors to fit the content into the target viewBox
        scale_x = TARGET_WIDTH / width
        scale_y = TARGET_HEIGHT / height
        scale = min(scale_x, scale_y)  # Maintain aspect ratio
        
        # Apply scaling to the group
        group_transform = group.attrib.get("transform", "")
        group.attrib["transform"] = f"{group_transform} scale({scale})".strip()
        
        # Set the new viewBox
        root.attrib["viewBox"] = TARGET_VIEWBOX
        
        # Save the modified SVG back to the file
        try:
            tree.write(filepath, encoding="utf-8", xml_declaration=True)
            print(f"{filename}: Successfully updated.")
        except Exception as e:
            print(f"Error saving {filename}: {e}")

