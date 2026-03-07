import asyncio
import hashlib
import os
import uuid

import aiofiles
import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from control.database.DatabaseManager import get_db, db_manager

load_dotenv()
PATH = os.getenv("DATA_PATH")
RELEVANT_COUNT = int(os.getenv("RELEVANT_COUNT"))
RELEVANT_CPU_PRIORITY = float(os.getenv("RELEVANT_CPU_PRIORITY"))
RELEVANT_RAM_PRIORITY = float(os.getenv("RELEVANT_RAM_PRIORITY"))
RELEVANT_DISK_PRIORITY = float(os.getenv("RELEVANT_DISK_PRIORITY"))
CHUNK_SIZE_MB = int(os.getenv("CHUNK_SIZE_MB"))
router = APIRouter(
    prefix="/file",
    tags=["File"]
)


# TODO() Think about adding file, chunk, chunk_storage data into database only after its writing

async def find_online_nodes(db: AsyncSession) -> dict[str, list[float]]:
    storages = await db_manager.get_storages()
    online_storages = {}

    async with httpx.AsyncClient() as client:
        tasks = []
        for node in storages:
            address = f"{node.ip}:{node.port}"
            tasks.append(client.get(f"http://{address}/api/status", timeout=0.2))

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for i, response in enumerate(responses):
            if isinstance(response, httpx.Response) and response.status_code == 200:
                node = storages[i]
                address = f"{node.ip}:{node.port}"
                data = response.json()
                disk_free = float(data["disk_total_gb"]) - float(data["disk_usage_gb"])
                online_storages[address] = [float(data["cpu_usage"]), float(data["memory_usage"]), disk_free]

    return online_storages


async def get_most_relevant(online_storages: dict) -> list[str]:
    node_quality = dict()
    for node, status in online_storages.items():
        node_quality[node] = int(
            (100 / (status[0] + 1)) * RELEVANT_CPU_PRIORITY +
            (100 / (status[1] + 1)) * RELEVANT_RAM_PRIORITY +
            (status[2] * RELEVANT_DISK_PRIORITY)
        )
    print(node_quality)
    relevant = sorted(node_quality.items(), key=lambda x: x[1], reverse=True)
    return [node[0] for node in relevant[:RELEVANT_COUNT]]


async def upload_chunk_to_node(client: httpx.AsyncClient, node_url: str, chunk_data: bytes,
                               chunk_index: int, file_name: str, chunk_uuid: str, db: AsyncSession):
    try:
        response = await client.post(f"http://{node_url}/api/file/{chunk_uuid}", content=chunk_data, timeout=60.0)
        if response.status_code == 200:
            print(f"Блок {chunk_uuid}({chunk_index}) загружен на ноду {node_url}")
            await db_manager.save_chunk_storage_info(chunk_uuid, node_url)
            return True
        else:
            print(f"Нода {node_url} ответила ошибкой {response.status_code}")
            return False
    except Exception as e:
        print(f"Ошибка при отправке блока {chunk_index} на {node_url}: {e}")
        return False


async def process_file_upload(file: UploadFile, file_name: str, target_nodes: list, db: AsyncSession):
    chunk_index = 0

    async with httpx.AsyncClient() as client:
        while True:
            chunk_data = await file.read(CHUNK_SIZE_MB * 1024 * 1024)
            chunk_uuid = str(uuid.uuid4())

            if not chunk_data:
                break

            await db_manager.save_chunk_info(chunk_uuid, file_name, chunk_index)
            tasks = [
                upload_chunk_to_node(client, node, chunk_data, chunk_index, file_name, chunk_uuid, db)
                for node in target_nodes
            ]

            results = await asyncio.gather(*tasks)

            if sum(results) < int(
                    len(target_nodes) / 2) + 1:  # Например, если меньше 2 нод приняли блок — это успех или ошибка?
                raise Exception(f"Ошибка репликации блока {chunk_index}. Запись остановлена.")

            print(f"Блок {chunk_index} успешно записан на {sum(results)} нод.")
            chunk_index += 1

    return {"status": "complete", "total_chunks": chunk_index}


@router.post("/upload")
async def upload_file(file: UploadFile, db: AsyncSession = Depends(get_db)):
    original_name = file.filename

    target_nodes = await get_most_relevant(await find_online_nodes(db))

    if not target_nodes:
        raise HTTPException(status_code=503, detail="Нет доступных нод")

    print(f"Начита загрузка файла: {original_name}")
    try:
        await db_manager.save_file_info(original_name)
        result = await process_file_upload(file, original_name, target_nodes, db)

        return {
            "filename": original_name,
            "chunks": result['total_chunks'],
            "nodes": target_nodes,
            "status": "success"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении блоков: {str(e)}")
