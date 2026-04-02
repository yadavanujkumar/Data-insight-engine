from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.db_models import Entity, Relationship
from app.schemas.schemas import EntityCreate, RelationshipCreate


class GraphService:
    def __init__(self, db: Session):
        self.db = db

    def create_entity(self, entity_data: EntityCreate) -> Entity:
        entity = Entity(
            name=entity_data.name,
            entity_type=entity_data.entity_type,
            properties=entity_data.properties or {},
            dataset_id=entity_data.dataset_id,
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def get_entity(self, entity_id: int) -> Optional[Entity]:
        return self.db.query(Entity).filter(Entity.id == entity_id).first()

    def list_entities(self, skip: int = 0, limit: int = 50) -> List[Entity]:
        return self.db.query(Entity).offset(skip).limit(limit).all()

    def create_relationship(self, rel_data: RelationshipCreate) -> Relationship:
        rel = Relationship(
            source_id=rel_data.source_id,
            target_id=rel_data.target_id,
            relationship_type=rel_data.relationship_type,
            weight=rel_data.weight,
            properties=rel_data.properties or {},
        )
        self.db.add(rel)
        self.db.commit()
        self.db.refresh(rel)
        return rel

    def list_relationships(self, skip: int = 0, limit: int = 50) -> List[Relationship]:
        return self.db.query(Relationship).offset(skip).limit(limit).all()

    def get_neighbors(self, entity_id: int, depth: int = 1) -> Dict[str, Any]:
        entity = self.get_entity(entity_id)
        if not entity:
            return {"error": "Entity not found"}

        visited_ids = {entity_id}
        nodes = [{"id": entity.id, "name": entity.name, "type": entity.entity_type}]
        edges = []
        current_frontier = [entity_id]

        for _ in range(depth):
            next_frontier = []
            rels = (
                self.db.query(Relationship)
                .filter(
                    (Relationship.source_id.in_(current_frontier))
                    | (Relationship.target_id.in_(current_frontier))
                )
                .all()
            )
            for rel in rels:
                edges.append({
                    "source": rel.source_id,
                    "target": rel.target_id,
                    "type": rel.relationship_type,
                    "weight": rel.weight,
                })
                for neighbor_id in [rel.source_id, rel.target_id]:
                    if neighbor_id not in visited_ids:
                        visited_ids.add(neighbor_id)
                        next_frontier.append(neighbor_id)
                        neighbor = self.get_entity(neighbor_id)
                        if neighbor:
                            nodes.append({"id": neighbor.id, "name": neighbor.name, "type": neighbor.entity_type})
            current_frontier = next_frontier

        return {"nodes": nodes, "edges": edges, "depth": depth}

    def get_stats(self) -> Dict[str, Any]:
        entity_count = self.db.query(Entity).count()
        rel_count = self.db.query(Relationship).count()
        return {
            "total_entities": entity_count,
            "total_relationships": rel_count,
            "density": round(rel_count / max(entity_count * (entity_count - 1), 1), 4),
        }
