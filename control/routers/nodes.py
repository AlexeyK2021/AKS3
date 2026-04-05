import os

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from control.controllers.database_controller import get_db, db_get_storages, db_manager, create_storage, commit_session, \
    delete_storage, get_storage_by_id
from control.log import log
from control.controllers.models import EntityTypeEnum, ActionTypeEnum

router = APIRouter(
    prefix="/node",
    tags=["Node"]
)

load_dotenv()
PROMETHEUS_URL=os.getenv("PROMETHEUS_URL")

@router.get("/")
async def get_nodes(db: AsyncSession = Depends(get_db)):
    session = await db_manager.get_session()
    nodes = await db_get_storages(session)
    await db_manager.close_session()
    return {"nodes": nodes}


class NodeRequest(BaseModel):
    ip: str
    port: int
    access_key: str
    secret_key: str


@router.post("/")
async def create_node(node: NodeRequest, session: AsyncSession = Depends(get_db)):

    storages = await db_get_storages(session)
    if (node.ip, node.port) in [(s.ip, s.port) for s in storages]:
        await log(
            entity_name=f"{node.ip}:{node.port}",
            entity_type=EntityTypeEnum.STORAGE,
            action=ActionTypeEnum.ADD,
            description="В системе уже есть такая нода хранения",
            success=False,
            session=session
        )
        raise HTTPException(status_code=409, detail=f"В системе уже есть нода хранения {node.ip}:{node.port}")

    async with httpx.AsyncClient() as client:
        try:
            status = await client.get(f"http://{node.ip}:{node.port}/minio/health/live", timeout=0.2)

            if status.status_code != 200:
                await log(
                    entity_name=f"{node.ip}:{node.port}",
                    entity_type=EntityTypeEnum.STORAGE,
                    action=ActionTypeEnum.ADD,
                    description="Хост недоступен",
                    success=False,
                    session=session
                )
                raise HTTPException(status_code=400, detail=f"Хост {node.ip}:{node.port} недоступен")

        except httpx.ConnectTimeout:
            await log(
                entity_name=f"{node.ip}:{node.port}",
                entity_type=EntityTypeEnum.STORAGE,
                action=ActionTypeEnum.ADD,
                description="Хост недоступен",
                success=False,
                session=session
            )
            raise HTTPException(status_code=400, detail=f"Хост {node.ip}:{node.port} недоступен")

    await create_storage(node.ip, node.port, node.access_key, node.secret_key, session)
    await log(
        entity_name=f"{node.ip}:{node.port}",
        entity_type=EntityTypeEnum.STORAGE,
        action=ActionTypeEnum.ADD,
        description="",
        success=True,
        session=session
    )
    await commit_session(session)
    await db_manager.close_session()
    return 201


@router.delete("/{node_id}")
async def delete_node(node_id: int, session: AsyncSession = Depends(get_db)):
    storages = await db_get_storages(session)

    if node_id not in [n.id for n in storages]:
        await log(
            entity_name=f"ID:{node_id}",
            entity_type=EntityTypeEnum.STORAGE,
            action=ActionTypeEnum.REMOVE,
            description="В системе нет ноды",
            success=False,
            session=session
        )
        raise HTTPException(status_code=400, detail=f"В системе нет ноды с id={node_id}")

    await delete_storage(node_id, session)
    await log(
        entity_name=f"ID:{node_id}",
        entity_type=EntityTypeEnum.STORAGE,
        action=ActionTypeEnum.REMOVE,
        description="",
        success=True,
        session=session
    )
    await commit_session(session)
    await db_manager.close_session()
    return 200


@router.get("/{node_id}/status")
async def get_node_status(node_id: int, session: AsyncSession = Depends(get_db)):
    node = await get_storage_by_id(node_id, session)
    node_instance = f"{node.ip}:{node.port}"
    queries = {
        "free_space_bytes": f'minio_node_drive_free_bytes{{instance="{node_instance}"}}',
        "total_space_bytes": f'minio_node_drive_total_bytes{{instance="{node_instance}"}}',
        "io_utilization": f'minio_node_drive_utilization_percent{{instance="{node_instance}"}}',
        "io_wait_avg": f'minio_node_drive_waiting_io_time_seconds{{instance="{node_instance}"}}',
        "uptime": f'minio_node_process_uptime_seconds{{instance="{node_instance}"}}',
        "is_up": f'up{{instance="{node_instance}"}}'
    }
    if node is None:
        raise HTTPException(status_code=404, detail=f"Хост c id={node_id} не зарегистрирован в системе")

    results = {}

    async with httpx.AsyncClient() as client:
        for metric_name, query in queries.items():
            try:
                response = await client.get(
                    f"{PROMETHEUS_URL}/api/v1/query",
                    params={'query': query}
                )
                data = response.json()

                if data['status'] == 'success' and data['data']['result']:
                    value = data['data']['result'][0]['value'][1]
                    results[metric_name] = float(value)
                else:
                    results[metric_name] = None

                if results.get("free_space_bytes") and results.get("total_space_bytes"):
                    free = results["free_space_bytes"]
                    total = results["total_space_bytes"]
                    results["free_percent"] = round((free / total) * 100, 2)
            except Exception as e:
                print(f"Ошибка при запросе {metric_name}: {e}")
                results[metric_name] = "Error"

    return {"metrics": results}
