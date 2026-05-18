# # analysis/health.py
# from soft_archmap.core.graph import DependencyGraph

# def compute_health(model):
#     """
#     Simple health metric: ratio of used entities to total entities.
#     """
#     graph = DependencyGraph()
#     for r in model.relations:
#         graph.add_edge(r.src, r.dst)

#     total = len(model.entities)
#     unused = len([e for e in model.entities.values() if not graph.dependents(e.id)])
#     score = (total - unused) / total if total else 1.0
#     return round(score, 2)

# analysis/health.py
from soft_archmap.analysis.cycles import detect_cycles
from soft_archmap.analysis.top_risk import TopRiskAnalyzer
from soft_archmap.core.graph import DependencyGraph

def compute_health(model):
    """
    Compute an overall health score (0-100) based on:
      - cycles
      - top risk modules
      - dependency density
      - impact potential
    """

    # ------------------
    # 1. Cycles factor
    # ------------------
    cycles = detect_cycles(model)
    cycle_penalty = min(len(cycles), 10) / 10  # max 10 cycles

    # ------------------
    # 2. Top-risk factor
    # ------------------
    risk_analyzer = TopRiskAnalyzer(model)
    top_risk = risk_analyzer.get_top_risk_modules()
    risk_penalty = min(len(top_risk["top_risk"]), 10) / 10

    # ------------------
    # 3. Dependency density factor
    # ------------------
    graph = getattr(model, "graph", None)
    if graph:
        total_deps = sum(len(graph.neighbors(n)) for n in graph.nodes())
        avg_deps = total_deps / max(len(graph.nodes()), 1)
        dep_penalty = min(avg_deps / 10, 1)  # 10+ deps is max penalty
    else:
        dep_penalty = 0

    # ------------------
    # 4. Impact potential factor
    # ------------------
    # Simplified: max outgoing edges count
    if graph:
        max_out = max((len(graph.neighbors(n)) for n in graph.nodes()), default=0)
        impact_penalty = min(max_out / 10, 1)
    else:
        impact_penalty = 0

    # ------------------
    # Combine factors
    # ------------------
    penalties = (cycle_penalty, risk_penalty, dep_penalty, impact_penalty)
    avg_penalty = sum(penalties) / len(penalties)
    health_score = max(0, int((1 - avg_penalty) * 100))

    return {
        "score": health_score,
        "cycles": len(cycles),
        "top_risk_count": len(top_risk["top_risk"]),
        "avg_dependencies": avg_deps if graph else 0,
        "max_impact": max_out if graph else 0
    }