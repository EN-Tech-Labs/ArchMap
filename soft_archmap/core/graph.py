from collections import defaultdict


class DependencyGraph:
    def __init__(self):
        # node -> {neighbor: set(relation_types)}
        self.adj = defaultdict(lambda: defaultdict(set))

        # reverse graph
        self.rev_adj = defaultdict(lambda: defaultdict(set))

    # ----------------------------
    # BUILD GRAPH
    # ----------------------------
    def add_edge(self, src: str, dst: str, rel_type: str = "depends"):
        self.adj[src][dst].add(rel_type)
        self.rev_adj[dst][src].add(rel_type)

    def build_from_model(self, model, allowed_types=None):
        """
        Build graph from ArchitectureModel
        """
        for r in model.relations:
            if allowed_types and r.type not in allowed_types:
                continue

            self.add_edge(r.src, r.dst, r.type)

    # ----------------------------
    # BASIC QUERIES
    # ----------------------------
    def nodes(self):
        return set(self.adj.keys()) | set(self.rev_adj.keys())

    def neighbors(self, node, rel_type=None):
        if node not in self.adj:
            return set()

        if rel_type:
            return {
                n for n, types in self.adj[node].items()
                if rel_type in types
            }

        return set(self.adj[node].keys())

    def dependents(self, node):
        return set(self.rev_adj.get(node, {}).keys())

    # ----------------------------
    # CYCLE DETECTION (IMPROVED)
    # ----------------------------
    def find_cycles(self):
        visited = set()
        stack = []
        stack_set = set()
        cycles = set()

        def normalize_cycle(cycle):
            """
            Normalize cycle to avoid duplicates:
            rotate so smallest node is first
            """
            min_node = min(cycle)
            min_index = cycle.index(min_node)
            rotated = cycle[min_index:] + cycle[:min_index]
            return tuple(rotated)

        def dfs(node):
            visited.add(node)
            stack.append(node)
            stack_set.add(node)

            for neighbor in self.adj.get(node, {}):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in stack_set:
                    idx = stack.index(neighbor)
                    cycle = stack[idx:]
                    cycles.add(normalize_cycle(cycle))

            stack.pop()
            stack_set.remove(node)

        for node in self.nodes():
            if node not in visited:
                dfs(node)

        return [list(c) for c in cycles]

    # ----------------------------
    # ADVANCED ANALYSIS
    # ----------------------------
    def find_dependency_chain(self, start, end, max_depth=10):
        """
        Find path from start → end
        """
        paths = []

        def dfs(node, path):
            if len(path) > max_depth:
                return

            if node == end:
                paths.append(path[:])
                return

            for neighbor in self.adj.get(node, {}):
                if neighbor not in path:
                    dfs(neighbor, path + [neighbor])

        dfs(start, [start])
        return paths

    def subgraph(self, nodes):
        """
        Extract subgraph
        """
        g = DependencyGraph()
        for src in nodes:
            for dst, types in self.adj.get(src, {}).items():
                if dst in nodes:
                    for t in types:
                        g.add_edge(src, dst, t)
        return g