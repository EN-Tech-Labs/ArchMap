import re
from collections import defaultdict
from archmap_python.core.model import ArchitectureModel

def sanitize_id(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", value)

def escape_label(value: str) -> str:
    return value.replace('"', r'\"').replace("\n", r"\n")

def node_style(entity_type: str):
    styles = {
        "module": ("folder", "#ECEFF1"),
        "class": ("box", "#E3F2FD"),
        "function": ("oval", "#E8F5E9"),
        "method": ("oval", "#FFF3E0"),
    }
    return styles.get(entity_type, ("box", "#FFFFFF"))

def edge_style(relation_type: str):
    styles = {
        "imports": 'style=dashed color="#546E7A"',
        "calls": 'color="#2E7D32"',
        "inherits": 'arrowhead=empty color="#1565C0"',
        "contains": 'arrowhead=none color="#616161"',
    }
    return styles.get(relation_type, "")

def export_graphviz(model, path="architecture.dot", group_by_file=True):
    """
    Export ArchitectureModel to Graphviz DOT format
    """
    lines = []
    lines.append("digraph Architecture {")
    lines.append("  rankdir=LR;")
    lines.append("  fontname=\"Helvetica\";")
    lines.append("  node [fontname=\"Helvetica\", style=filled];")
    lines.append("  edge [fontname=\"Helvetica\"];")
    lines.append("")

    # Group by file
    entities_by_file = defaultdict(list)
    for e in sorted(model.entities.values(), key=lambda x: (x.file, x.type, x.name)):
        entities_by_file[e.file].append(e)

    for file_name, entities in sorted(entities_by_file.items()):
        cluster_name = sanitize_id(f"cluster_{file_name}")
        if group_by_file:
            lines.append(f'  subgraph {cluster_name} {{')
            lines.append(f'    label="module: {escape_label(file_name)}";')
            lines.append("    style=rounded;")

        for e in entities:
            safe_id = sanitize_id(e.id)
            label = f"{e.type}\\n{escape_label(e.name)}"
            shape, color = node_style(e.type)
            lines.append(
                f'    "{safe_id}" [label="{label}", shape={shape}, fillcolor="{color}"];'
            )

        if group_by_file:
            lines.append("  }")
            lines.append("")

    # Add edges
    for r in sorted(model.relations, key=lambda x: (x.type, x.src, x.dst)):
        src_id = sanitize_id(r.src)
        dst_id = sanitize_id(r.dst)
        style = edge_style(r.type)
        lines.append(
            f'  "{src_id}" -> "{dst_id}" [label="{r.type}" {style}];'
        )

    # Legend
    lines.append("""
  subgraph cluster_legend {
    label="Legend";
    fontsize=12;
    style=dashed;

    key_module [label="module", shape=folder, fillcolor="#ECEFF1"];
    key_class [label="class", shape=box, fillcolor="#E3F2FD"];
    key_function [label="function", shape=oval, fillcolor="#E8F5E9"];
    key_method [label="method", shape=oval, fillcolor="#FFF3E0"];
  }
""")
    lines.append("}")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"✅ Graphviz DOT exported to {path}")