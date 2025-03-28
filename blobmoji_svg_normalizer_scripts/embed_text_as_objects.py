#!/usr/bin/env python3
'''
Unlike other scripts in this folder, this one is not intended for in-place execution. It should
only be used against folders that contain SVGs that require manipulation. Additionally, any fonts
used in the SVGs must be installed. This script also uses Inkscape for processing.
'''
import os
import subprocess
import glob
import argparse
import re

def clean_font_attributes(svg_file):
    """
    Clean font-related attributes from an SVG file after text-to-path conversion.
    
    Args:
        svg_file: Path to the SVG file to clean
    """
    try:
        # Read the SVG file content
        with open(svg_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Define font attributes to remove (both in style attributes and as standalone XML attributes)
        font_attributes = [
            'font-family',
            '-inkscape-font-specification',
            'font-weight',
            'font-size',
            'letter-spacing',
            'word-spacing'
        ]
        
        # Remove font attributes from style declarations
        for attr in font_attributes:
            content = re.sub(r'{0}:[^;"]+;?'.format(attr), '', content)
        
        # Remove font attributes as standalone XML attributes
        for attr in font_attributes:
            content = re.sub(r'{0}="[^"]+"'.format(attr), '', content)
        
        # Clean up any double spaces in style attributes that might have been left
        content = re.sub(r'style="([^"]*)\s{2,}([^"]*)"', r'style="\1 \2"', content)
        
        # Clean up empty style attributes
        content = re.sub(r'style="\s*"', '', content)
        
        # Handle consecutive semicolons in style attributes
        content = re.sub(r';\s*;', ';', content)
        
        # Ensure style attributes don't start or end with semicolons
        content = re.sub(r'style="\s*;', r'style="', content)
        content = re.sub(r';\s*"', r'"', content)
        
        # Write the cleaned content back to the file
        with open(svg_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return True
    except Exception as e:
        print(f"Error cleaning font attributes: {e}")
        return False

def convert_svg_text_to_path(input_file, output_file=None):
    """
    Convert all text in an SVG file to paths using Inkscape's command line.
    
    Args:
        input_file: Path to the input SVG file
        output_file: Path to save the output SVG file. If None, will use a temp file and replace original.
    """
    if output_file is None:
        temp_file = input_file + ".temp.svg"
        final_file = input_file
    else:
        temp_file = output_file
        final_file = output_file
    
    try:
        # Step 1: Use Inkscape to convert text to paths and export as plain SVG
        cmd = [
            "inkscape",
            "--export-filename={}".format(temp_file),
            "--export-plain-svg",
            "--export-text-to-path",
            input_file
        ]
        
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Step 2: Clean any remaining font attributes from the file
        clean_font_attributes(temp_file)
        
        # Step 3: If we used a temp file, replace the original
        if output_file is None:
            os.replace(temp_file, final_file)
            
        print(f"Successfully processed {input_file} to {final_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error processing {input_file}: {e}")
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return False

def batch_convert_svgs(input_dir, output_dir=None, pattern="*.svg"):
    """
    Process all SVG files in a directory that match the given pattern.
    
    Args:
        input_dir: Directory containing SVG files
        output_dir: Directory to save converted files. If None, overwrites original files.
        pattern: Glob pattern to match SVG files
    """
    # Get list of SVG files
    svg_files = glob.glob(os.path.join(input_dir, pattern))
    
    if not svg_files:
        print(f"No SVG files found in {input_dir} matching pattern {pattern}")
        return
    
    success_count = 0
    for svg_file in svg_files:
        if output_dir:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate output filename
            filename = os.path.basename(svg_file)
            output_file = os.path.join(output_dir, filename)
            
            if convert_svg_text_to_path(svg_file, output_file):
                success_count += 1
        else:
            # Overwrite original file
            if convert_svg_text_to_path(svg_file):
                success_count += 1
    
    print(f"Successfully processed {success_count} of {len(svg_files)} SVG files")

def main():
    parser = argparse.ArgumentParser(description="Convert all text in SVG files to paths and remove all font-related attributes")
    parser.add_argument("input", help="Input directory or single SVG file")
    parser.add_argument("-o", "--output", help="Output directory (for batch conversion) or file (for single file)")
    parser.add_argument("-p", "--pattern", default="*.svg", help="File pattern for batch conversion (default: *.svg)")
    
    args = parser.parse_args()
    
    if os.path.isdir(args.input):
        # Batch conversion
        batch_convert_svgs(args.input, args.output, args.pattern)
    elif os.path.isfile(args.input):
        # Single file conversion
        convert_svg_text_to_path(args.input, args.output)
    else:
        print(f"Error: Input path {args.input} does not exist")

if __name__ == "__main__":
    main()

