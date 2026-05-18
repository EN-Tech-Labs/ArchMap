class ImpactAnalyzer:
    def __init__(self, model):
        self.graph = model.graph

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

        return {
            "target": target,
            "impact_count": len(result),
            "impacted_nodes": result
        }