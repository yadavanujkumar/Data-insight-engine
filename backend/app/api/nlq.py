from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.schemas import NLQRequest, NLQResponse
from app.services.nlq_service import NLQService

router = APIRouter()


@router.post("/nlq/query", response_model=NLQResponse)
def natural_language_query(request: NLQRequest, db: Session = Depends(get_db)):
    service = NLQService(db)
    return service.process_query(request)
