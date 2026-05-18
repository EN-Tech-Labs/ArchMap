import os
from soft_archmap.export.graphviz import export_graphviz
from soft_archmap.analysis.visualize import visualize_architecture

def generate_html_report(model, graph, analysis, output_dir=None, svg_path=None):
    """
    Generate a professional HTML report for architecture analysis
    """
    output_dir = output_dir or os.getcwd()
    reports_dir = os.path.join(output_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)

    # Paths
    dot_path = os.path.join(reports_dir, "architecture.dot")
    svg_path = svg_path or os.path.join(reports_dir, "architecture.svg")
    html_path = os.path.join(reports_dir, "report.html")

    # Export DOT & SVG
    export_graphviz(model, dot_path)
    visualize_architecture(dot_path, svg_path)

    # Build entity table
    entity_rows = "".join(
        f"<tr><td>{e.id}</td><td>{e.type}</td><td>{e.name}</td><td>{e.file}</td></tr>\n"
        for e in model.entities.values()
    )

    # Build relation table
    relation_rows = "".join(
        f"<tr><td>{r.src}</td><td>{r.dst}</td><td>{r.type}</td><td>{r.weight}</td></tr>\n"
        for r in model.relations
    )

    # Build insights section
    insights_html = ""
    if "insights" in analysis:
        for i in analysis["insights"]:
            reasons = "<ul>" + "".join(f"<li>{r}</li>" for r in i["reasons"]) + "</ul>"
            insights_html += f"<div class='insight'><h4>{i['severity']} - {i['node']}</h4>{reasons}</div>"

    # HTML template
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Architecture Analysis Report</title>
<style>
    body {{ font-family: Arial, sans-serif; margin: 20px; }}
    h1 {{ color: #2E7D32; }}
    h2 {{ border-bottom: 2px solid #ccc; padding-bottom: 5px; }}
    table {{ border-collapse: collapse; width: 100%; margin-bottom: 30px; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
    th {{ background-color: #f2f2f2; }}
    .insight {{ border: 1px solid #eee; padding: 10px; margin-bottom: 10px; background: #fafafa; }}
    .summary {{ display: flex; gap: 40px; margin-bottom: 30px; }}
    .summary div {{ border: 1px solid #ccc; padding: 10px; flex: 1; background: #f9f9f9; }}
    #graph {{ width: 100%; height: 600px; border: 1px solid #ccc; }}
</style>
</head>
<body>
<h1>Architecture Analysis Report</h1>

<div class="summary">
    <div><h3>Health Score</h3><p>{analysis.get('health', 'N/A')}</p></div>
    <div><h3>Cycles</h3><p>{len(analysis.get('cycles', []))}</p></div>
    <div><h3>Top Risk Nodes</h3><p>{", ".join([n for n, s in analysis.get('top_risk', {}).get('top_risk', [])[:5]])}</p></div>
</div>

<h2>Architecture Graph</h2>
<object type="image/svg+xml" data="{os.path.basename(svg_path)}" width="100%" height="600px"></object>

<h2>Insights</h2>
{insights_html or "<p>No critical insights found.</p>"}

<h2>Entities</h2>
<table>
    <thead>
        <tr><th>ID</th><th>Type</th><th>Name</th><th>File</th></tr>
    </thead>
    <tbody>
        {entity_rows}
    </tbody>
</table>

<h2>Relations</h2>
<table>
    <thead>
        <tr><th>Source</th><th>Destination</th><th>Type</th><th>Weight</th></tr>
    </thead>
    <tbody>
        {relation_rows}
    </tbody>
</table>

</body>
</html>
    """

    # Write HTML file
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ HTML report generated: {html_path}")