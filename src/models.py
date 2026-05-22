from typing import Optional
from datetime import datetime
from sqlalchemy import (
    ForeignKey, Integer, Unicode, DateTime, func, 
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Department(Base):
    __tablename__ = "departments"
    
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(Unicode(200), nullable=False)
    employees: Mapped[list["Employee"]] = relationship(
        back_populates="department", cascade="all, delete"
    )
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE")
    )
    parent: Mapped[Optional["Department"]] = relationship(
        back_populates="children", remote_side=[id], lazy="selectin", join_depth=1
    )
    children: Mapped[list["Department"]] = relationship(
        back_populates="parent", passive_deletes=True,
        lazy="selectin", join_depth=1
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(), 
        nullable=False
    )
    
    def is_name_unique_among_children(self, name: str) -> bool:
        for child in self.children:
            if child.name == name:
                return False
        return True


class Employee(Base):
    __tablename__ = "employees"
    
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    full_name: Mapped[str] = mapped_column(Unicode(200), nullable=False, unique=True)
    position: Mapped[str] = mapped_column(Unicode(200), nullable=False, unique=False)
    
    department_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=False
    )
    department: Mapped["Department"] = relationship(back_populates="employees")
    
    hired_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, 
        default=None, 
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(), 
        nullable=False
    )






























