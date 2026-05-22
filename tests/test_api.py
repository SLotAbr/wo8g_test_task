import pytest
import urllib
from datetime import datetime
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models import Employee, Department


@pytest.mark.asyncio
async def test_department_registration(client: AsyncClient, db_session: AsyncSession) -> None:
    fake_department = {"name":"department_1"}
    response = await client.post("/departments/", json=fake_department)
    assert response.status_code == 201
    assert response.json()["id"] == 1
    assert response.json()["parent_id"] == None
    
    fake_department = {"name":"department_2", "parent_id":1}
    response = await client.post("/departments/", json=fake_department)
    assert response.status_code == 201
    assert response.json()["id"] == 2
    assert response.json()["parent_id"] == 1
    name_repetition = {"name":"department_2", "parent_id":1}
    response = await client.post("/departments/", json=name_repetition)
    assert response.status_code == 422
    assert response.json()["detail"] is not None
    
    # One parent + 5 recursion levels
    for level in range(3,7): # [3,4,5,6]
        fake_dep = {"name":"dep_"+str(level), "parent_id":level-1}
        response = await client.post("/departments/", json=fake_dep)
        assert response.status_code == 201
        assert response.json()["id"] == level
        assert response.json()["parent_id"] == level-1
    fake_dep = {"name":"dep_7", "parent_id":6}
    response = await client.post("/departments/", json=fake_dep)
    assert response.status_code == 422
    assert response.json()["detail"] is not None


@pytest.mark.asyncio
async def test_employee_registration(client: AsyncClient, db_session: AsyncSession) -> None:
    fake_department = {"name":"department_1"}
    response = await client.post("/departments/", json=fake_department)
    assert response.status_code == 201
    assert response.json()["id"] == 1
    assert response.json()["parent_id"] == None
    
    fake_employee = {"full_name":"name", "position":"position"}
    response = await client.post("/departments/1/employees", json=fake_employee)
    assert response.status_code == 201
    
    hired_at = datetime.now()
    fake_employee = {
        "full_name":"name_2", 
        "position":"position", 
        "hired_at":hired_at.isoformat()
    }
    response = await client.post("/departments/1/employees", json=fake_employee)
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_get_department(client: AsyncClient, db_session: AsyncSession) -> None:
    """
    dep1 | dep2 | dep3
                | dep4 | dep5
    """
    fake_department = {"name":"department_1"}
    response = await client.post("/departments/", json=fake_department)
    assert response.status_code == 201
    assert response.json()["id"] == 1
    assert response.json()["parent_id"] == None
    
    fake_department = {"name":"department_2", "parent_id":1}
    response = await client.post("/departments/", json=fake_department)
    assert response.status_code == 201
    assert response.json()["id"] == 2
    assert response.json()["parent_id"] == 1
    
    fake_department = {"name":"department_3", "parent_id":2}
    response = await client.post("/departments/", json=fake_department)
    assert response.status_code == 201
    assert response.json()["id"] == 3
    assert response.json()["parent_id"] == 2
    
    fake_department = {"name":"department_4", "parent_id":2}
    response = await client.post("/departments/", json=fake_department)
    assert response.status_code == 201
    assert response.json()["id"] == 4
    assert response.json()["parent_id"] == 2
    
    fake_department = {"name":"department_5", "parent_id":4}
    response = await client.post("/departments/", json=fake_department)
    assert response.status_code == 201
    assert response.json()["id"] == 5
    assert response.json()["parent_id"] == 4
    
    fake_employee = {"full_name":"name", "position":"position"}
    response = await client.post("/departments/4/employees", json=fake_employee)
    assert response.status_code == 201
    
    fake_employee = {"full_name":"name_2", "position":"position"}
    response = await client.post("/departments/5/employees", json=fake_employee)
    assert response.status_code == 201
    
    data = {"depth":1,"include_employees":False}
    path_query = urllib.parse.urlencode(data)
    response = await client.get("/departments/1?"+path_query)
    assert response.status_code == 200
    assert response.json()["department"]["name"] == "department_1"
    assert len(response.json()["children"]) == 1
    assert len(response.json()["children"][0]["children"]) == 0
    assert "employees" not in response.json()
    assert "employees" not in response.json()["children"][0]
    
    data = {"depth":2,"include_employees":True}
    path_query = urllib.parse.urlencode(data)
    response = await client.get("/departments/1?"+path_query)
    assert response.status_code == 200
    assert len(response.json()["children"]) == 1
    assert len(response.json()["children"][0]["children"]) == 2 # dep2
    assert response.json()["children"][0]["children"][0]["department"]["name"] == "department_3"
    assert "employees" not in response.json()["children"][0]["children"][0]
    assert len(response.json()["children"][0]["children"][0]["children"]) == 0
    #
    assert response.json()["children"][0]["children"][1]["department"]["name"] == "department_4"
    assert "employees" in response.json()["children"][0]["children"][1]
    assert len(response.json()["children"][0]["children"][1]["employees"]) == 1
    assert response.json()["children"][0]["children"][1]["employees"][0]["full_name"] == "name"
    assert len(response.json()["children"][0]["children"][1]["children"]) == 0 # no dep5


@pytest.mark.asyncio
async def test_patch_department(client: AsyncClient, db_session: AsyncSession) -> None:
    fake_department = {"name":"department_1"}
    response = await client.post("/departments/", json=fake_department)
    assert response.status_code == 201
    assert response.json()["id"] == 1
    assert response.json()["parent_id"] == None
    
    fake_department = {"name":"department_2", "parent_id":1}
    response = await client.post("/departments/", json=fake_department)
    assert response.status_code == 201
    assert response.json()["id"] == 2
    assert response.json()["parent_id"] == 1
    
    fake_department = {"name":"department_3", "parent_id":2}
    response = await client.post("/departments/", json=fake_department)
    assert response.status_code == 201
    assert response.json()["id"] == 3
    assert response.json()["parent_id"] == 2
    
    # PATCH tests
    


@pytest.mark.asyncio
async def test_cascade_delete_department(client: AsyncClient, db_session: AsyncSession) -> None:
    fake_department = {"name":"department_1"}
    response = await client.post("/departments/", json=fake_department)
    assert response.status_code == 201
    assert response.json()["id"] == 1
    assert response.json()["parent_id"] == None
    
    fake_department = {"name":"department_2", "parent_id":1}
    response = await client.post("/departments/", json=fake_department)
    assert response.status_code == 201
    assert response.json()["id"] == 2
    assert response.json()["parent_id"] == 1
    
    fake_department = {"name":"department_3", "parent_id":2}
    response = await client.post("/departments/", json=fake_department)
    assert response.status_code == 201
    assert response.json()["id"] == 3
    assert response.json()["parent_id"] == 2
    
    fake_department = {"name":"department_4", "parent_id":3}
    response = await client.post("/departments/", json=fake_department)
    assert response.status_code == 201
    assert response.json()["id"] == 4
    assert response.json()["parent_id"] == 3
    
    fake_employee = {"full_name":"name", "position":"position"}
    response = await client.post("/departments/4/employees", json=fake_employee)
    assert response.status_code == 201
    
    data = {"mode":"cascade"}
    path_query = urllib.parse.urlencode(data)
    response = await client.delete("/departments/4?"+path_query)
    assert response.status_code == 204
    
    results = await db_session.execute(select(Employee))
    results = results.scalars().all()
    assert len(results) == 0
    results = await db_session.execute(select(Department))
    results = results.scalars().all()
    assert len(results) == 3
    
    # 
    
    fake_employee = {"full_name":"name_2", "position":"position"}
    response = await client.post("/departments/3/employees", json=fake_employee)
    assert response.status_code == 201
    fake_employee = {"full_name":"name_3", "position":"position"}
    response = await client.post("/departments/3/employees", json=fake_employee)
    assert response.status_code == 201
    
    data = {"mode":"cascade"}
    path_query = urllib.parse.urlencode(data)
    response = await client.delete("/departments/1?"+path_query)
    assert response.status_code == 204
    
    results = await db_session.execute(select(Department))
    results = results.scalars().all()
    assert len(results) == 0
    results = await db_session.execute(select(Employee))
    results = results.scalars().all()
    assert len(results) == 0


@pytest.mark.asyncio
async def test_reassign_delete_department(client: AsyncClient, db_session: AsyncSession) -> None:
    fake_department = {"name":"department_1"}
    response = await client.post("/departments/", json=fake_department)
    assert response.status_code == 201
    assert response.json()["id"] == 1
    assert response.json()["parent_id"] == None
    
    fake_department = {"name":"department_2", "parent_id":1}
    response = await client.post("/departments/", json=fake_department)
    assert response.status_code == 201
    assert response.json()["id"] == 2
    assert response.json()["parent_id"] == 1
    
    fake_department = {"name":"department_3", "parent_id":2}
    response = await client.post("/departments/", json=fake_department)
    assert response.status_code == 201
    assert response.json()["id"] == 3
    assert response.json()["parent_id"] == 2
    
    fake_employee = {"full_name":"name_1", "position":"position"}
    response = await client.post("/departments/2/employees", json=fake_employee)
    assert response.status_code == 201
    fake_employee = {"full_name":"name_2", "position":"position"}
    response = await client.post("/departments/2/employees", json=fake_employee)
    assert response.status_code == 201
    
    data = {"mode":"reassign","reassign_to_department_id":1}
    path_query = urllib.parse.urlencode(data)
    response = await client.delete("/departments/2?"+path_query)
    assert response.status_code == 204
    
    results = await db_session.execute(select(Employee))
    results = results.scalars().all()
    assert len(results) == 2
    assert results[0].department_id == 1
    assert results[1].department_id == 1
    
    result = await db_session.execute(select(Department).where(Department.id==3))
    result = result.scalar_one_or_none()
    assert result.parent_id == None





























