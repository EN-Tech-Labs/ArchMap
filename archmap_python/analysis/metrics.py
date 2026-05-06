# analysis/metrics.py
from archmap_python.core.graph import DependencyGraph

def compute_metrics(model):
    """
    Compute simple architecture metrics.
    """
    graph = DependencyGraph()
    for r in model.relations:
        graph.add_edge(r.src, r.dst)

    num_modules = sum(1 for e in model.entities.values() if e.type == "module")
    num_classes = sum(1 for e in model.entities.values() if e.type == "class")
    num_functions = sum(1 for e in model.entities.values() if e.type == "function")
    num_relations = len(model.relations)
    num_cycles = len(graph.find_cycles())

    return {
        "modules": num_modules,
        "classes": num_classes,
        "functions": num_functions,
        "relations": num_relations,
        "cycles": num_cycles
    }