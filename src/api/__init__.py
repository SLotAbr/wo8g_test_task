from fastapi import APIRouter
from .departments import DepartmentsRouter


router = APIRouter()
router.include_router(
    DepartmentsRouter, prefix="/departments", tags=["departments"]
)

