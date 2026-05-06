from archmap_python.analysis.risk import RiskEngine


# class TopRiskAnalyzer:
#     def __init__(self, graph):
#         self.graph = graph
#         self.risk_engine = RiskEngine(graph)

#     def get_top_risk_modules(self, top_k=10):
#         scores = []

#         for node in self.graph.nodes():
#             score = self.risk_engine.compute_risk(node)
#             scores.append((node, score))

#         # sort by risk descending
#         scores.sort(key=lambda x: x[1], reverse=True)

#         return {
#             "top_risk": scores[:top_k]
#         }

class TopRiskAnalyzer:
    def __init__(self, model):
        self.model = model
        self.graph = model.graph
        self.engine = RiskEngine(self.graph)

    def get_top_risk_modules(self):
        results = []

        for node_id, entity in self.model.entities.items():

            # 🚫 SKIP EXTERNAL CODE HERE
            if entity.type == "external":
                continue

            score = self.engine.compute_risk(node_id)
            results.append((node_id, score))

        results.sort(key=lambda x: x[1], reverse=True)

        return {
            "top_risk": results[:10]
        }