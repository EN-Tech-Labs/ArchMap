import json
from soft_archmap.core.model import ArchitectureModel

def export_json(model, path="architecture.json"):
    """
    Export ArchitectureModel to JSON
    """
    data = {
        "entities": [],
        "relations": []
    }

    for e in model.entities.values():
        data["entities"].append({
            "id": e.id,
            "type": e.type,
            "name": e.name,
            "file": e.file
        })

    for r in model.relations:
        data["relations"].append({
            "src": r.src,
            "dst": r.dst,
            "type": r.type
        })

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"✅ JSON exported to {path}")