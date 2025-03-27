#!/usr/bin/env python3
import os
import xml.etree.ElementTree as ET
from pathlib import Path

# Register the SVG namespace for proper parsing
ET.register_namespace("", "http://www.w3.org/2000/svg")
SVG_NS = {"svg": "http://www.w3.org/2000/svg"}

# Hardcoded path to the "svg" folder
SVG_FOLDER = "svg"

def find_svg_with_text(directory=SVG_FOLDER):
    """
    Scan a directory for SVG files containing text elements.
    
    Args:
        directory: Path to the directory containing SVG files, defaults to "svg"
    
    Returns:
        List of SVG filenames containing text elements
    """
    svg_with_text = []
    
    # Ensure directory exists
    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' does not exist.")
        return svg_with_text
        
    # Get all SVG files in the directory
    svg_files = [f for f in os.listdir(directory) if f.lower().endswith('.svg')]
    
    print(f"Found {len(svg_files)} SVG files in '{directory}' folder. Scanning for text elements...")
    
    for svg_file in svg_files:
        file_path = os.path.join(directory, svg_file)
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Look for text elements using various SVG text tags
            text_elements = root.findall(".//svg:text", SVG_NS) or root.findall(".//text")
            tspan_elements = root.findall(".//svg:tspan", SVG_NS) or root.findall(".//tspan")
            textPath_elements = root.findall(".//svg:textPath", SVG_NS) or root.findall(".//textPath")
            
            if text_elements or tspan_elements or textPath_elements:
                svg_with_text.append(svg_file)
        except Exception as e:
            print(f"Error processing {svg_file}: {e}")
    
    return svg_with_text

def main():
    svg_files_with_text = find_svg_with_text()
    
    if not svg_files_with_text:
        print("No SVG files with text elements found (or directory might not exist).")
        return
        
    print(f"\nFound {len(svg_files_with_text)} SVG files containing text elements:")
    for file in svg_files_with_text:
        print(f"- {file}")
    
    # Optional: Save results to a file
    output_file = "svg_with_text.txt"
    with open(output_file, 'w') as f:
        for file in svg_files_with_text:
            f.write(f"{file}\n")
    print(f"\nResults saved to {output_file}")

if __name__ == "__main__":
    main()
