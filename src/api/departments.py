from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_async_session
from src.models import Department, Employee
from src import schemas
from src.api.utils import (
    get_department_or_404, 
    check_employee_name,
    check_names_within_department,
    get_department_subtree_ids,
    check_recursion_level,
    check_loops,
    get_department_tree
)


DepartmentsRouter = APIRouter()


@DepartmentsRouter.post("/", status_code=status.HTTP_201_CREATED)
async def register_department(
    register_department: schemas.RegisterDepartment,
    session: AsyncSession = Depends(get_async_session),
) -> schemas.ReadDepartment:
    """Регистрирует новое подразделение."""
    registration_dict = register_department.model_dump(exclude_unset=True)
    registration_dict["name"] = registration_dict["name"].strip()
    
    department = Department(name=registration_dict["name"])
    if (parent_id:=registration_dict.get("parent_id")):
        parent_department = await get_department_or_404(parent_id, session)
        check_names_within_department(
            parent_department, registration_dict["name"]
        )
        await check_recursion_level(parent_department, session)
        department.parent = parent_department
    session.add(department)
    await session.commit()
    return department


@DepartmentsRouter.post("/{id}/employees", status_code=status.HTTP_201_CREATED)
async def register_employee(
    register_employee: schemas.RegisterEmployee,
    department: Department = Depends(get_department_or_404),
    session: AsyncSession = Depends(get_async_session),
) -> schemas.ReadEmployee:
    """Создаёт сотрудника в выбранном подразделении."""
    registration_dict = register_employee.model_dump(exclude_unset=True)
    await check_employee_name(registration_dict["full_name"], session)
    employee = Employee(**registration_dict)
    employee.department = department
    session.add(employee)
    await session.commit()
    return employee



@DepartmentsRouter.get("/{id}")
async def get_department(
    search_query: Annotated[schemas.InspectDepartmentTree, Query()],
    department: Department = Depends(get_department_or_404),
    session: AsyncSession = Depends(get_async_session),
) -> schemas.DepartmentTreeNode:
    """Предоставляет информацию о поддереве с выбранным подразделением во главе."""
    return await get_department_tree(
        department, 
        search_query.depth, 
        search_query.include_employees, 
        session
    )


@DepartmentsRouter.patch("/{id}")
async def patch_department(
    patch_department: schemas.PatchDepartment,
    department: Department = Depends(get_department_or_404),
    session: AsyncSession = Depends(get_async_session),
) -> schemas.ReadDepartment:
    """Обновляет имя департамента или прикрепляет его к другому родителю."""
    patch_dict = patch_department.model_dump(exclude_unset=True)

    # name=1, parent_id=0
    if patch_dict.get("name") and not patch_dict.get("parent_id"):
        if department.parent_id:
            parent = await get_department_or_404(department.parent_id, session)
            check_names_within_department(parent, patch_dict["name"])
        department.name = patch_dict["name"]

    # parent_id=1
    if (parent_id:=patch_dict.get("parent_id")):
        if department.id == parent_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
                detail="Department cannot be its own parent"
            )
        new_parent = await get_department_or_404(parent_id, session)
        await check_loops(parent_id, department, session)
        await check_recursion_level(new_parent, session)
        department.parent = new_parent
        # name=1
        if patch_dict.get("name"):
            check_names_within_department(new_parent, patch_dict["name"])
            department.name = patch_dict["name"]

    session.add(department)
    await session.commit()
    return department


@DepartmentsRouter.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    delete_query: Annotated[schemas.DeleteDepartment, Query()],
    department: Department = Depends(get_department_or_404),
    session: AsyncSession = Depends(get_async_session),
) -> None:
    """Предоставляет интерфейс для удаления департаментов в одном из 2 режимов. 
    "cascade" удаляет все элементы поддерева с выбранным подразделением во главе, 
    включая само головное подразделение и всех прикреплённых сотрудников. 
    "reassign" удаляет только выбранное подразделение, переводя всех его 
    сотрудников в департамент с номером "reassign_to_department_id​".
    """
    delete_dict = delete_query.model_dump(exclude_unset=True)

    if delete_dict["mode"]==schemas.DeleteMode.REASSIGN:
        if not delete_dict.get("reassign_to_department_id"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="reassign_to_department_id must be provided for the 'reassign' mode"
            )
        new_department = await get_department_or_404(
            delete_dict["reassign_to_department_id"], session
        )
        await session.refresh(department, ["employees"])
        for employee in list(department.employees):
            employee.department = new_department

    else: # delete_dict["mode"]==schemas.DeleteMode.CASCADE
        if department.children:
            delete_list = await get_department_subtree_ids(
                department, session
            )
            for delete_id in delete_list:
                await session.delete(
                    await get_department_or_404(delete_id, session)
                )

    await session.delete(department)
    await session.commit()



















