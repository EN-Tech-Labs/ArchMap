from collections import defaultdict, deque
from soft_archmap.core.graph import DependencyGraph

class ImpactAnalyzer:
    def __init__(self, model):
        # Build a dependency graph from the model
        self.graph = DependencyGraph()
        self.graph.build_from_model(model)

    def analyze(self, target):
        visited = set()
        result = []

        def dfs(node):
            for dep in self.graph.dependents(node):
                if dep not in visited:
                    visited.add(dep)
                    result.append(dep)
                    dfs(dep)

        dfs(target)
        return result