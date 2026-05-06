# analysis/cycles.py
from archmap_python.core.graph import DependencyGraph

def detect_cycles(model):
    """
    Detect cycles in architecture.
    Returns a list of cycles (list of entity IDs).
    """
    graph = DependencyGraph()
    for r in model.relations:
        graph.add_edge(r.src, r.dst)

    return graph.find_cycles()