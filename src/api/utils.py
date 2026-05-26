from fastapi import Depends, status, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_async_session
from src.models import Department, Employee
from src import schemas


async def get_department_or_404(
    id: int, 
    session: AsyncSession = Depends(get_async_session),
) -> Department:
    query = select(Department).where(Department.id == id)
    query = await session.scalars(query)
    department = query.one_or_none()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Department with given id is not found"
        )
    return department


async def department_has_max_recursion_level(
    recursion_parent_id: int, 
    session: AsyncSession = Depends(get_async_session),
) -> bool:
    for recursion_level in range(2,6):
        recursion_object = await get_department_or_404(
            recursion_parent_id, session
        )
        if not (recursion_parent_id:=recursion_object.parent_id):
            return False
    return True


async def check_employee_name(
    name: str, session: AsyncSession = Depends(get_async_session),
) -> None:
    query = select(Employee).filter(Employee.full_name == name)
    query = await session.scalars(query)
    employee = query.one_or_none()
    if employee:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail="Employee with this name already exists"
        )


async def get_department_subtree_ids(
    root: Department,
    session: AsyncSession = Depends(get_async_session),
) -> list[int]:
    q, id_list = [], []
    q.extend(root.children)
    while True:
        v = q.pop(0)
        id_list.append(v.id)
        await session.refresh(v, ["children"])
        if (c:=v.children):
            q.extend(c)
        if len(q)==0:
            break
    return id_list


def check_names_within_department(department: Department, name: str) -> None:
    if not department.is_name_unique_among_children(name):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The name must be unique within one parent department"
        )


async def check_recursion_level(
    new_department: Department, 
    session: AsyncSession
) -> None:
    if new_department.parent_id and await department_has_max_recursion_level(
        new_department.parent_id, session
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Maximum recursion level is reached"
        )


async def check_loops(
    parent_id:int, 
    department: Department, 
    session: AsyncSession
) -> None:
    id_list = await get_department_subtree_ids(department, session)
    if parent_id in id_list:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Loops are forbidden for this data structure"
        )


async def get_department_tree(
    root: Department,
    depth: int,
    include_employees: bool,
    session: AsyncSession,
) -> schemas.DepartmentTreeNode:
    children_list, employees = [], []
    await session.refresh(root, ["children"])
    
    if depth >0:
        for child in root.children:
            children_list.append(
                await get_department_tree(
                    child, depth-1, include_employees, session
                )
            )
    
    if include_employees:
        select_query = select(Employee)\
                .where(Employee.department_id==root.id)\
                .order_by(Employee.created_at.desc())
        results = await session.execute(select_query)
        for employee in results.scalars().all():
            employees.append(
                schemas.ReadEmployee(**employee.__dict__)
            )
    
    pydantic_dict = schemas.DepartmentTreeNode(
        department=schemas.ReadDepartment(**root.__dict__),
        employees=employees,
        children=children_list
    )
    return pydantic_dict






















