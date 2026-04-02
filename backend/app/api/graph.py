from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.schemas import EntityCreate, EntityRead, RelationshipCreate, RelationshipRead
from app.services.graph_service import GraphService

router = APIRouter()


@router.post("/graph/entities", response_model=EntityRead)
def create_entity(entity: EntityCreate, db: Session = Depends(get_db)):
    service = GraphService(db)
    return service.create_entity(entity)


@router.get("/graph/entities", response_model=List[EntityRead])
def list_entities(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    service = GraphService(db)
    return service.list_entities(skip, limit)


@router.get("/graph/entities/{entity_id}", response_model=EntityRead)
def get_entity(entity_id: int, db: Session = Depends(get_db)):
    service = GraphService(db)
    entity = service.get_entity(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.post("/graph/relationships", response_model=RelationshipRead)
def create_relationship(rel: RelationshipCreate, db: Session = Depends(get_db)):
    service = GraphService(db)
    return service.create_relationship(rel)


@router.get("/graph/relationships", response_model=List[RelationshipRead])
def list_relationships(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    service = GraphService(db)
    return service.list_relationships(skip, limit)


@router.get("/graph/neighbors/{entity_id}")
def get_neighbors(entity_id: int, depth: int = 1, db: Session = Depends(get_db)):
    service = GraphService(db)
    return service.get_neighbors(entity_id, depth)


@router.get("/graph/stats")
def graph_stats(db: Session = Depends(get_db)):
    service = GraphService(db)
    return service.get_stats()
