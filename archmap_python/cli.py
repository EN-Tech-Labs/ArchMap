import os
import sys

from archmap_python.core.model import ArchitectureModel
from archmap_python.adapters.python_adapter import PythonParser
from archmap_python.export.graphviz import export_graphviz
from archmap_python.export.json_export import export_json
from archmap_python.analysis.cycles import detect_cycles
from archmap_python.analysis.health import compute_health
from archmap_python.analysis.metrics import compute_metrics
from archmap_python.analysis.impact import ImpactAnalyzer
from archmap_python.analysis.risk import RiskEngine
from archmap_python.analysis.top_risk import TopRiskAnalyzer


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
        from archmap_python.core.graph import DependencyGraph
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

        output_dir = self.get_output_dir()

        json_path = os.path.join(output_dir, "architecture.json")
        dot_path = os.path.join(output_dir, "architecture.dot")

        export_json(self.model, json_path)
        export_graphviz(self.model, dot_path)

        print("\n--- ANALYSIS COMPLETE ---")
        print("Cycles:", detect_cycles(self.model))
        print("Health:", compute_health(self.model))
        print("Metrics:", compute_metrics(self.model))
        print("Analysis complete.")

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
            result.extend(analyzer.analyze(t))

        # Remove duplicates
        result = list(set(result))
        result.sort(key=lambda x: ("module" in x, "class" in x, "function" in x))

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
        print("""
Usage:
  archmap analyze <repo_path>
  archmap impact <repo_path> <node>
  archmap report <repo_path>              -----> not yet available
  archmap top-risk <repo_path>
        """)

def main():
    # Display welcome message and contact info
    border = '\n' + '=' * 100 + '\n'
    lines = [
        border,
        "You are using ArchMap-Python by Excited Nuclei Tech Labs",
        "For feedback, please email: excitednuclei.techlabs@gmail.com",
        border
    ]

    # Print each line centered in a terminal width of 100
    for line in lines:
        print(line.center(100))

    # Run the command-line interface
    CLI().run()

if __name__ == "__main__":
    # CLI().run()
    main()