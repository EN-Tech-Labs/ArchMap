# analysis/health.py
from archmap_python.core.graph import DependencyGraph

def compute_health(model):
    """
    Simple health metric: ratio of used entities to total entities.
    """
    graph = DependencyGraph()
    for r in model.relations:
        graph.add_edge(r.src, r.dst)

    total = len(model.entities)
    unused = len([e for e in model.entities.values() if not graph.dependents(e.id)])
    score = (total - unused) / total if total else 1.0
    return round(score, 2)