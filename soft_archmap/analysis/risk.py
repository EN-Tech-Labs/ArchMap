class RiskEngine:
    def __init__(self, graph):
        self.graph = graph

    # -------------------------
    # CORE RISK SCORE
    # -------------------------
    def compute_risk(self, node_id):
        direct = len(self.graph.dependents(node_id))

        # indirect risk (2-hop approximation)
        indirect = 0
        for child in self.graph.dependents(node_id):
            indirect += len(self.graph.dependents(child))

        # cycle penalty
        cycles = self._in_cycle(node_id)
        cycle_penalty = 2 if cycles else 0

        risk_score = (
            direct * 0.6 +
            indirect * 0.2 +
            cycle_penalty * 0.2
        )

        return round(risk_score, 3)

    # -------------------------
    # CHECK IF NODE IN CYCLE
    # -------------------------
    def _in_cycle(self, node_id):
        cycles = self.graph.find_cycles()
        return any(node_id in cycle for cycle in cycles)