from collections import defaultdict


class InsightBuilder:
    def __init__(self, model, graph, analysis_results):
        self.model = model
        self.graph = graph
        self.analysis = analysis_results

    # -------------------------
    # PUBLIC API
    # -------------------------
    def build(self):
        insights = []

        insights.extend(self._cycle_insights())
        insights.extend(self._risk_insights())

        return {
            "insights": sorted(
                insights,
                key=lambda x: x["severity_rank"],
                reverse=True
            )
        }

    # -------------------------
    # CYCLE INSIGHTS
    # -------------------------
    def _cycle_insights(self):
        results = []

        for cycle in self.analysis["cycles"]:
            for node in cycle:
                results.append({
                    "type": "cycle",
                    "node": node,
                    "severity": "HIGH",
                    "severity_rank": 3,
                    "reasons": [
                        f"part of dependency cycle: {cycle}"
                    ],
                    "impact": list(self.graph.dependents(node))
                })

        return results 

    # -------------------------
    # RISK INSIGHTS
    # -------------------------
    def _risk_insights(self):
        results = []

        for node, score in self.analysis["top_risk"]["top_risk"]:
            entity = self.model.entities.get(node)
            if not entity:
                continue

            reasons = self._explain_risk(node)

            severity = "LOW"
            rank = 1

            if score > 5:
                severity = "HIGH"
                rank = 3
            elif score > 2:
                severity = "MEDIUM"
                rank = 2

            results.append({
                "type": "risk",
                "node": node,
                "severity": severity,
                "severity_rank": rank,
                "score": score,
                "reasons": reasons,
                "impact": list(self.graph.dependents(node))
            })

        return results

    # -------------------------
    # EXPLANATIONS (IMPORTANT)
    # -------------------------
    def _explain_risk(self, node):
        reasons = []

        dependents = len(self.graph.dependents(node))
        if dependents > 3:
            reasons.append(f"high fan-in ({dependents} dependents)")

        cycles = self.analysis["cycles"]
        if any(node in c for c in cycles):
            reasons.append("participates in dependency cycle")

        if len(self.graph.neighbors(node)) > 5:
            reasons.append("high coupling (many outgoing dependencies)")

        if not reasons:
            reasons.append("moderate dependency exposure")

        return reasons