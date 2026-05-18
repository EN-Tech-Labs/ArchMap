import os
import sys
VERSION = "0.2.1"
from soft_archmap.core.model import ArchitectureModel
from soft_archmap.adapters.python_adapter import PythonParser
from soft_archmap.export.graphviz import export_graphviz
from soft_archmap.export.json_export import export_json
from soft_archmap.analysis.cycles import detect_cycles
from soft_archmap.analysis.health import compute_health
from soft_archmap.analysis.metrics import compute_metrics
from soft_archmap.analysis.impact import ImpactAnalyzer
from soft_archmap.analysis.risk import RiskEngine
from soft_archmap.analysis.top_risk import TopRiskAnalyzer
from soft_archmap.engine.analysis_engine import AnalysisEngine
from soft_archmap.engine.insight_builder import InsightBuilder
from soft_archmap.report.html_report import generate_html_report
from soft_archmap.analysis.visualize import generate_visual

class CLI:
    def __init__(self):
        self.args = sys.argv
        self.command = self.args[1] if len(self.args) > 1 else None
        self.input_repo = self.args[2] if len(self.args) > 2 else None
        self.target = self.args[3] if len(self.args) > 3 else None

        self.model = None
        self.graph = None
        self.parsed = False  # avoid multiple parses

    # -------------------------
    # ENTRY POINT
    # -------------------------
    def run(self):
        # Global flags
        if self.command in ["--help", "-h"]:
            self.help()
            return

        if self.command in ["--version", "-v"]:
            self.version()
            return

        if not self.command:
            self.help()
            return

        command_map = {
            "analyze": self.analyze,
            "impact": self.impact,
            "report": self.report,
            "top-risk": self.top_risk
        }

        handler = command_map.get(self.command)

        if not handler:
            print(f"Unknown command: {self.command}")
            self.help()
            return

        # Parse repo first if command needs it
        if self.command in ["analyze", "impact", "top-risk"]:
            if not self.input_repo:
                print("Error: repo path is required for this command")
                return
            self.parse_repo()

        # Execute command
        handler()

    # -------------------------
    # PARSING REPO ONCE
    # -------------------------
    def parse_repo(self):
        if self.parsed:
            return

        if not self.input_repo or not os.path.isdir(self.input_repo):
            print("Invalid repository path")
            sys.exit(1)

        print(f"Parsing repository: {self.input_repo} ...")
        self.model = ArchitectureModel()
        parser = PythonParser(self.input_repo, self.model)

        for root, dirs, files in os.walk(self.input_repo):
            dirs[:] = [d for d in dirs if d not in {
                    "venv", ".venv", "env", ".env",
                    "__pycache__", ".git",
                    "build", "dist",
                    ".mypy_cache", ".pytest_cache"}]
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    print(f"Parsing {file_path}")
                    parser.parse_file(file_path)

        # Ensure we have a dependency graph

        from soft_archmap.core.graph import DependencyGraph
        
        if not hasattr(self.model, "graph") or self.model.graph is None:
            self.model.graph = DependencyGraph()
            self.model.graph.build_from_model(self.model)

        self.graph = self.model.graph
        self.parsed = True
        print("Repository parsed successfully.\n")

    # -------------------------
    # COMMANDS
    # -------------------------
    def analyze(self):
        print(f"Analyzing repo: {self.input_repo}")

        # 1️⃣ Get output directory and create subfolders
        output_dir = self.get_output_dir()
        os.makedirs(output_dir, exist_ok=True)

        report_dir = os.path.join(output_dir, "reports")
        os.makedirs(report_dir, exist_ok=True)

        # 2️⃣ Run analysis engine
        engine = AnalysisEngine(self.model)
        analysis = engine.run()  # should include health, cycles, top_risk, etc.

        # 3️⃣ Build insights
        insight_builder = InsightBuilder(
            self.model,
            self.graph,
            analysis
        )
        insights = insight_builder.build()
        analysis['insights'] = insights["insights"]

        # 4️⃣ Export JSON & DOT
        export_json(self.model, os.path.join(report_dir, "architecture.json"))
        export_graphviz(self.model, os.path.join(report_dir, "architecture.dot"))

        # 5️⃣ Print insights (CLI UX)
        print("\n--- 🔴 INSIGHTS ---")
        for i in analysis['insights'][:10]:
            print(f"\n[{i['severity']}] {i['node']}")
            for r in i["reasons"]:
                print(f"  - {r}")

        # 6️⃣ Summary
        print("\n--- SUMMARY ---")
        print(f"Health: {analysis['health']}")
        print(f"Cycles: {len(analysis['cycles'])}")
        print(f"Top Risk Nodes: {analysis['top_risk']['top_risk'][:3]}")

        # 7️⃣ Generate visualization
        svg_path = os.path.join(report_dir, "architecture.svg")
        png_path = os.path.join(report_dir, "architecture.png")
        try:
            generate_visual(self.model, report_dir)
            print(f"SVG architecture visualization saved: {svg_path}")
        except Exception as e:
            print("Graphviz not found or error generating SVG. PNG fallback will be used.")
            generate_visual(self.model, report_dir, output_format="png")
            print(f"PNG architecture visualization saved: {png_path}")

        # 8️⃣ Generate HTML report
        html_path = os.path.join(report_dir, "report.html")
        try:
            generate_html_report(
                model=self.model,
                graph=self.graph,
                analysis=analysis,
                output_dir=report_dir,
                svg_path=svg_path  # optional: pass SVG to embed in HTML
            )
            print(f"HTML report generated: {html_path}")
        except PermissionError:
            print(f"Permission denied writing HTML report at {html_path}. Try closing any open report or use another folder.")

    def impact(self):
        if not self.target:
            print("Error: target is required for impact analysis")
            return

        targets = self.resolve_target(self.target)
        if not targets:
            print(f"No entities matched target '{self.target}'")
            return

        analyzer = ImpactAnalyzer(self.model)
        result = []
        for t in targets:
            impact_result = analyzer.analyze(t)  # assuming this returns a dict
            if isinstance(impact_result, dict) and "impacted_nodes" in impact_result:
                result.extend(impact_result["impacted_nodes"])
            else:
                result.extend(impact_result)  # fallback if it's a list
        
        # Remove duplicates
        result = list(set(result))
        result.sort()  # simple sort; modify if you want custom key
        
        print("\n--- IMPACT RESULT ---")
        print({
            "target": self.target,
            "impact_count": len(result),
            "impacted_nodes": result
        })

    def top_risk(self):
        analyzer = TopRiskAnalyzer(self.model)
        # analyzer = TopRiskAnalyzer(self.graph)
        result = analyzer.get_top_risk_modules()

        print("\n--- TOP RISK MODULES ---")
        for node, score in result["top_risk"]:
            print(f"{node} -> {score}")

    # -------------------------
    # HELPERS
    # -------------------------
    def resolve_target(self, target: str):
        if not target:
            return []

        matches = []
        for eid, entity in self.model.entities.items():
            file_match = entity.file and target in entity.file
            name_match = target == entity.name
            id_match = target == eid
            if file_match or name_match or id_match:
                matches.append(eid)

        return list(set(matches))

    def report(self):
        print("[REPORT GENERATION] pending....")

    def get_output_dir(self):
        """
        Ask user for output directory with validation.
        Falls back to current working directory.
        """

        while True:
            path = input("Enter output directory path (press Enter for default): ").strip()

            # fallback case
            if not path:
                print(f"Using default path: {os.getcwd()}")
                return os.getcwd()

            # valid path
            if os.path.isdir(path):
                return os.path.abspath(path)

            # try creating it
            try:
                os.makedirs(path, exist_ok=True)
                print(f"Created and using: {path}")
                return os.path.abspath(path)
            except Exception:
                print("Invalid path. Try again.")

    def help(self):
        print(f"""
    Soft ArchMap v{VERSION}

    Usage:
    soft-archmap analyze <repo_path>
    soft-archmap impact <repo_path> <node>
    soft-archmap report <repo_path>      (coming soon)
    soft-archmap top-risk <repo_path>

    Global Options:
    -h, --help       Show help
    -v, --version    Show version

    Examples:
    soft-archmap analyze ./my_repo
    soft-archmap impact ./my_repo UserService
    """)

    def version(self):
        print(f"Soft ArchMap v{VERSION}")

def main():

    command = sys.argv[1] if len(sys.argv) > 1 else None

    # Minimal output for global flags
    if command not in ["--help", "-h", "--version", "-v"]:
        border = '\n' + '=' * 100 + '\n'
        lines = [
            border,
            f"Soft ArchMap v{VERSION} by Excited Nuclei Tech Labs",
            "Feedback & Support:",
            "mailto:excitednuclei.techlabs@gmail.com",
            border]

        for line in lines:
            print(line.center(100))

    CLI().run()

if __name__ == "__main__":
    # CLI().run()
    main()