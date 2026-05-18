from soft_archmap.analysis.cycles import detect_cycles
from soft_archmap.analysis.health import compute_health
from soft_archmap.analysis.metrics import compute_metrics
from soft_archmap.analysis.top_risk import TopRiskAnalyzer


class AnalysisEngine:
    def __init__(self, model):
        self.model = model
        self.graph = model.graph

    def run(self):
        cycles = detect_cycles(self.model)
        health = compute_health(self.model)
        metrics = compute_metrics(self.model)

        top_risk = TopRiskAnalyzer(self.model).get_top_risk_modules()

        return {
            "cycles": cycles,
            "health": health,
            "metrics": metrics,
            "top_risk": top_risk
        }