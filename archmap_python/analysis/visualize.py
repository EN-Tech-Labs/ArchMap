# analysis/visualize.py
import os
import subprocess
import shutil

def visualize_architecture(dot_file, output_file="architecture.png"):
    """
    Generate PNG from Graphviz DOT file.
    Requires 'dot' (Graphviz) installed.
    """
    # png_path = os.path.join(output_dir, "architecture.png")
    if not shutil.which("dot"):
        print("Graphviz 'dot' not found. Install Graphviz to generate visualization.")
        return

    try:
        subprocess.run(
            ["dot", "-Tpng", dot_file, "-o", output_file],
            check=True
        )
        print(f"✅ Architecture visualization saved to {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error generating visualization: {e}")