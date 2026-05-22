from typing import Optional
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


class RegisterDepartment(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    parent_id: Optional[int] = None


class RegisterEmployee(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    position: str = Field(min_length=1, max_length=200)
    hired_at: Optional[datetime] = None


class ReadDepartment(RegisterDepartment):
    id: int
    created_at: datetime


class ReadEmployee(RegisterEmployee):
    id: int
    department_id: int
    created_at: datetime


class InspectDepartmentTree(BaseModel):
    depth: int = Field(ge=1, le=5)
    include_employees: bool = True


class DepartmentTreeNode(BaseModel):
    department: ReadDepartment
    employees: Optional[list[ReadEmployee]] = Field(exclude_if=lambda v: not v)
    children: Optional[list]


class PatchDepartment(BaseModel):
    name: Optional[str] = Field(min_length=1, max_length=200)
    parent_id: Optional[int] = None


class DeleteMode(str, Enum):
    CASCADE: str = "cascade"
    REASSIGN: str = "reassign"


class DeleteDepartment(BaseModel):
    mode: DeleteMode
    reassign_to_department_id: Optional[int] = None


























