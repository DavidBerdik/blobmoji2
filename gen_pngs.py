#!/usr/bin/env python3
import os
import cairosvg
from multiprocessing import Pool, cpu_count

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

def convert_svg_to_png(args):
    svg_path, filename, dim = args
    name_without_ext = os.path.splitext(filename)[0]
    output_dir = os.path.join(output_base_dir, str(dim))
    output_path = os.path.join(output_dir, f"{name_without_ext}.png")
    try:
        cairosvg.svg2png(
            url=svg_path,
            write_to=output_path,
            output_width=dim,
            output_height=dim
        )
        return f"✓ Converted {filename} to {dim}x{dim} PNG."
    except Exception as e:
        return f"✗ Failed to convert {filename} at {dim}x{dim}: {e}"

# Gather all tasks
tasks = []
for filename in os.listdir(svg_dir):
    if filename.lower().endswith(".svg"):
        svg_path = os.path.join(svg_dir, filename)
        for dim in dimensions:
            tasks.append((svg_path, filename, dim))

# Detect number of logical CPU cores
num_processes = cpu_count()
print(f"Using {num_processes} processes for conversion.")

if __name__ == "__main__":
    with Pool(processes=num_processes) as pool:
        for result in pool.imap_unordered(convert_svg_to_png, tasks):
            print(result)

    print("✅ All done!")
