from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import Dataset
from app.schemas.schemas import SimulationRequest, SimulationResult
from app.services.simulation_service import SimulationService

router = APIRouter()


@router.post("/simulation/run", response_model=SimulationResult)
def run_simulation(request: SimulationRequest, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    service = SimulationService(db)
    return service.run(dataset, request)


@router.post("/simulation/whatif")
def run_whatif(request: SimulationRequest, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    service = SimulationService(db)
    return service.what_if(dataset, request)
