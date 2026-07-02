from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.dependencies import get_db, get_current_clinic_id
from schemas.dentist import (
    DentistCreate,
    DentistResponse,
    DentistResponseDetail
)
from services.dentist_service import (
    create_dentist,
)

router = APIRouter(
    prefix="/dentists",
    tags=["Dentists"]
)
