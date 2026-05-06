from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict


# ----------------------------
# ENTITY
# ----------------------------
@dataclass
class Entity:
    id: str
    type: str   # "module" | "class" | "function" | "method" | "external"
    name: str
    file: str
    line: Optional[int] = None   # NEW (useful later)


# ----------------------------
# RELATION
# ----------------------------
@dataclass
class Relation:
    src: str
    dst: str
    type: str   # "imports" | "contains" | "inherits" | "calls"
    weight: int = 1  # NEW: useful for call frequency


# ----------------------------
# ARCHITECTURE MODEL
# ----------------------------
@dataclass
class ArchitectureModel:
    entities: Dict[str, Entity] = field(default_factory=dict)
    relations: List[Relation] = field(default_factory=list)

    # NEW: for deduplication + fast lookup
    _relation_set: Set[Tuple[str, str, str]] = field(default_factory=set, init=False)
    _forward_index: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set), init=False)
    _reverse_index: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set), init=False)

    # ----------------------------
    # ENTITY METHODS
    # ----------------------------
    def add_entity(self, entity: Entity):
        """
        Add or update an entity.
        """
        self.entities[entity.id] = entity

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        return self.entities.get(entity_id)

    def ensure_entity(self, entity_id: str, entity_type="external", name=None, file="external"):
        """
        Create entity if it doesn't exist.
        """
        if entity_id not in self.entities:
            self.entities[entity_id] = Entity(
                id=entity_id,
                type=entity_type,
                name=name or entity_id.split(":", 1)[-1],
                file=file
            )

    # ----------------------------
    # RELATION METHODS
    # ----------------------------
    def add_relation(self, relation: Relation):
        key = (relation.src, relation.dst, relation.type)

        if key not in self._relation_set:
            self.relations.append(relation)
            self._relation_set.add(key)

            # build graph indexes
            self._forward_index[relation.src].add(relation.dst)
            self._reverse_index[relation.dst].add(relation.src)

        else:
            for r in self.relations:
                if (r.src, r.dst, r.type) == key:
                    r.weight += 1
                    break

    def dependencies(self, node_id: str) -> Set[str]:
        return self._forward_index.get(node_id, set())
    
    def dependents(self, node_id: str) -> Set[str]:
        return self._reverse_index.get(node_id, set())

    def get_relations(self, src=None, dst=None, type=None) -> List[Relation]:
        """
        Flexible query API (VERY useful later).
        """
        results = self.relations

        if src:
            results = [r for r in results if r.src == src]
        if dst:
            results = [r for r in results if r.dst == dst]
        if type:
            results = [r for r in results if r.type == type]

        return results