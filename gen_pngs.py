#!/usr/bin/env python3
import os
import cairosvg

# Input and output configuration
svg_dir = "svg"
output_base_dir = "png"
dimensions = [32, 72, 128, 512]

# Create the input folder if it doesn't exist
if not os.path.exists(svg_dir):
    os.makedirs(svg_dir)
    print(f"Created '{svg_dir}' folder. Please add SVG files to convert.")
    exit(0)

# Create output directories
for dim in dimensions:
    os.makedirs(os.path.join(output_base_dir, str(dim)), exist_ok=True)

# Process each SVG file
for filename in os.listdir(svg_dir):
    if filename.lower().endswith(".svg"):
        svg_path = os.path.join(svg_dir, filename)
        name_without_ext = os.path.splitext(filename)[0]

        for dim in dimensions:
            output_dir = os.path.join(output_base_dir, str(dim))
            output_path = os.path.join(output_dir, f"{name_without_ext}.png")

            try:
                cairosvg.svg2png(
                    url=svg_path,
                    write_to=output_path,
                    output_width=dim,
                    output_height=dim
                )
                print(f"✓ Converted {filename} to {dim}x{dim} PNG.")
            except Exception as e:
                print(f"✗ Failed to convert {filename} at {dim}x{dim}: {e}")

print("✅ All done!")
