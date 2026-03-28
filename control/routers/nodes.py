import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from control.DatabaseController import get_db, get_storages, db_manager, create_storage, commit_session, \
    delete_storage, get_storage_by_id

router = APIRouter(
    prefix="/node",
    tags=["Node"]
)


@router.get("/")
async def get_nodes(db: AsyncSession = Depends(get_db)):
    session = await db_manager.get_session()
    nodes = await get_storages(session)
    await db_manager.close_session()
    return {"nodes": nodes}


class NodeRequest(BaseModel):
    ip: str
    port: int


@router.post("/")
async def create_node(node: NodeRequest, db: AsyncSession = Depends(get_db)):
    session = await db_manager.get_session()

    storages = await get_storages(session)
    if (node.ip, node.port) in [(s.ip, s.port) for s in storages]:
        raise HTTPException(status_code=409, detail=f"В системе уже есть нода хранения {node.ip}:{node.port}")

    async with httpx.AsyncClient() as client:
        try:
            status = await client.get(f"http://{node.ip}:{node.port}/api/healthcheck", timeout=0.2)

            if status.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Хост {node.ip}:{node.port} недоступен")

        except httpx.ConnectTimeout:
            raise HTTPException(status_code=400, detail=f"Хост {node.ip}:{node.port} недоступен")

    await create_storage(node.ip, node.port, session)
    await commit_session(session)
    await db_manager.close_session()
    return 201


@router.delete("/{node_id}")
async def delete_node(node_id: int, db: AsyncSession = Depends(get_db)):
    session = await db_manager.get_session()
    storages = await get_storages(session)

    if node_id not in [n.id for n in storages]:
        raise HTTPException(status_code=400, detail=f"В системе нет ноды с id={node_id}")

    await delete_storage(node_id, session)
    await commit_session(session)
    await db_manager.close_session()
    return 200


@router.get("/{node_id}/status")
async def get_node_status(node_id: int, db: AsyncSession = Depends(get_db)):
    session = await db_manager.get_session()
    node = await get_storage_by_id(node_id, session)

    if node is None:
        raise HTTPException(status_code=404, detail=f"Хост c id={node_id} не зарегистрирован в системе")

    metrics = {}
    async with httpx.AsyncClient() as client:
        try:
            health = await client.get(f"http://{node.ip}:{node.port}/api/healthcheck", timeout=0.2)
            online = health.status_code == 200

            status_resp = await client.get(f"http://{node.ip}:{node.port}/api/status", timeout=0.2)
            if status_resp.status_code == 200:
                metrics = status_resp.json()  # <-- парсим JSON в словарь
            else:
                online = False
        except (httpx.ConnectTimeout, httpx.RequestError, ValueError) as e:
            online = False

    return {"online": online, "metrics": metrics}
