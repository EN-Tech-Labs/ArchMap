class RiskEngine:
    def __init__(self, graph):
        self.graph = graph

    def compute_risk(self, node_id):
        direct = len(self.graph.dependents(node_id))

        indirect = 0
        for child in self.graph.dependents(node_id):
            indirect += len(self.graph.dependents(child))

        in_cycle = self._in_cycle(node_id)
        cycle_penalty = 2 if in_cycle else 0

        score = (
            direct * 0.6 +
            indirect * 0.2 +
            cycle_penalty * 0.2
        )

        return round(score, 2)

    def explain(self, node_id):
        reasons = []

        if len(self.graph.dependents(node_id)) > 3:
            reasons.append("high fan-in")

        if self._in_cycle(node_id):
            reasons.append("in dependency cycle")

        if len(self.graph.dependencies(node_id)) > 5:
            reasons.append("high coupling")

        return reasons

    def _in_cycle(self, node_id):
        cycles = self.graph.find_cycles()
        return any(node_id in c for c in cycles)