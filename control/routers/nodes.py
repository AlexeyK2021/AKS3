import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from control.DatabaseController import get_db, get_storages, db_manager, create_storage, commit_session, \
    delete_storage

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
