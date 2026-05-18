class TopRiskAnalyzer:
    def __init__(self, model):
        self.model = model
        self.graph = model.graph

        from soft_archmap.analysis.risk import RiskEngine
        self.engine = RiskEngine(self.graph)

    def get_top_risk_modules(self):
        results = []

        for node_id, entity in self.model.entities.items():
            if entity.type == "external":
                continue

            score = self.engine.compute_risk(node_id)

            results.append((node_id, score))

        results.sort(key=lambda x: x[1], reverse=True)

        return {
            "top_risk": results[:10]
        }