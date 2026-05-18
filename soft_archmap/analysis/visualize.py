# analysis/visualize.py
import os
import subprocess
import shutil
# from soft_archmap.analysis.visualize import visualize_architecture
from soft_archmap.export.graphviz import export_graphviz

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

def generate_visual(model, output_dir="output"):
    dot_file = os.path.join(output_dir, "architecture.dot")
    png_file = os.path.join(output_dir, "architecture.png")
    # Export DOT
    export_graphviz(model, dot_file)
    # Generate PNG
    visualize_architecture(dot_file, png_file)
    print(f"Architecture visualization saved as {png_file}")