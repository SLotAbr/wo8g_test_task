from httpx import AsyncClient


async def POST_department(
    client: AsyncClient, 
    post_dict: dict, 
    check_dict: dict,
    response_status: int = 201,
) -> None:
    response = await client.post("/departments/", json=post_dict)
    assert response.status_code == response_status
    for key in check_dict:
        assert response.json()[key] == check_dict[key]

