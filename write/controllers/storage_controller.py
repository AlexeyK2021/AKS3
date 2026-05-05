import asyncio
import io
import os
import uuid

import httpx
import minio
from dotenv import load_dotenv
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from log import log
from controllers.database_controller import save_chunk_info, save_chunk_storage_info, get_storages, \
    make_chunk_active
from controllers.models import EntityTypeEnum, ActionTypeEnum

load_dotenv()
PATH = os.getenv("DATA_PATH")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME")
RELEVANT_COUNT = int(os.getenv("RELEVANT_COUNT"))
RELEVANT_CPU_PRIORITY = float(os.getenv("RELEVANT_CPU_PRIORITY"))
RELEVANT_RAM_PRIORITY = float(os.getenv("RELEVANT_RAM_PRIORITY"))
RELEVANT_DISK_PRIORITY = float(os.getenv("RELEVANT_DISK_PRIORITY"))
CHUNK_SIZE_MB = int(os.getenv("CHUNK_SIZE_MB"))


# async def find_online_nodes(session: AsyncSession) -> dict[str, list[float]]:
#     storages = await get_storages(session)
#     online_storages = {}
#
#     async with httpx.AsyncClient() as client:
#         tasks = []
#         for node in storages:
#             address = f"{node.ip}:{node.port}"
#             tasks.append(client.get(f"http://{address}/api/status", timeout=0.2))
#
#         responses = await asyncio.gather(*tasks, return_exceptions=True)
#
#         for i, response in enumerate(responses):
#             if isinstance(response, httpx.Response) and response.status_code == 200:
#                 node = storages[i]
#                 address = f"{node.ip}:{node.port}"
#                 data = response.json()
#                 disk_free = float(data["disk_total_gb"]) - float(data["disk_usage_gb"])
#                 online_storages[address] = [float(data["cpu_usage"]), float(data["memory_usage"]), disk_free]
#
#     return online_storages


async def get_node_weights() -> dict[str, float]:
    query = 'minio_node_drive_free_bytes'
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{PROMETHEUS_URL}/api/v1/query", params={'query': query})
            results = response.json()['data']['result']

            nodes_free_space = {
                res['metric']['instance']: int(res['value'][1])
                for res in results
            }
            return nodes_free_space
        except Exception as e:
            print(f"Ошибка получения метрик: {e}")
            return {}


async def get_most_relevant() -> list[str]:
    # node_quality = dict()
    # for node, status in online_storages.items():
    #     node_quality[node] = int(
    #         (100 / (status[0] + 1)) * RELEVANT_CPU_PRIORITY +
    #         (100 / (status[1] + 1)) * RELEVANT_RAM_PRIORITY +
    #         (status[2] * RELEVANT_DISK_PRIORITY)
    #     )
    # print(node_quality)
    # relevant = sorted(node_quality.items(), key=lambda x: x[1], reverse=True)
    nodes_free_space = await get_node_weights()
    if not nodes_free_space:
        raise Exception("Нет доступных нод для записи")
    return sorted(nodes_free_space, key=nodes_free_space.get, reverse=True)[:RELEVANT_COUNT]

    # return [node[0] for node in relevant[:RELEVANT_COUNT]]


async def upload_chunk_to_node(node_url: str, chunk_data: bytes,
                               chunk_index: int, chunk_uuid: str, session: AsyncSession) -> bool:
    storages = await get_storages(session)
    storage = None
    for s in storages:
        url = f"{s.ip}:{s.port}"
        if url == node_url:
            storage = s
            break
    try:
        minio_client = minio.Minio(
            endpoint=f"{storage.ip}:{storage.port}",
            access_key=storage.access_key,
            secret_key=storage.secret_key,
            secure=False
        )
        data_stream = io.BytesIO(chunk_data)
        data_size = len(chunk_data)

        minio_client.put_object(
            bucket_name=MINIO_BUCKET_NAME,
            object_name=chunk_uuid,
            data=data_stream,
            length=data_size,
            content_type="application/octet-stream"
        )
        await log(
            entity_name=f"{chunk_uuid}",
            entity_type=EntityTypeEnum.CHUNK,
            action=ActionTypeEnum.UPLOAD,
            description="",
            success=True,
            session=session
        )
        await save_chunk_storage_info(chunk_uuid, node_url, session)

        return True
    except Exception as e:
        print(e)
        await log(
            entity_name=f"{chunk_uuid}",
            entity_type=EntityTypeEnum.CHUNK,
            action=ActionTypeEnum.UPLOAD,
            description="Ошибка при отправке блока",
            success=False,
            session=session
        )
        return False


# async def process_file_upload(file: UploadFile, file_name: str, target_nodes: list, session: AsyncSession):
#     chunk_index = 0
#
#     async with httpx.AsyncClient() as client:
#         while True:
#             chunk_data = await file.read(CHUNK_SIZE_MB * 1024 * 1024)
#             chunk_uuid = str(uuid.uuid4())
#
#             if not chunk_data:
#                 break
#
#             await save_chunk_info(chunk_uuid, file_name, chunk_index, session)
#             tasks = [
#                 upload_chunk_to_node(client, node, chunk_data, chunk_index, chunk_uuid, session)
#                 for node in target_nodes
#             ]
#
#             results = await asyncio.gather(*tasks)
#
#             if sum(results) < RELEVANT_COUNT:
#                 raise Exception(f"Ошибка репликации блока {chunk_index}. Запись остановлена.")
#
#             print(f"Блок {chunk_index} успешно записан на {sum(results)} нод.")
#             chunk_index += 1
#
#     return {"status": "complete", "total_chunks": chunk_index}


async def process_file_upload(file: UploadFile, file_name: str, target_nodes: list, session: AsyncSession):
    chunk_index = 0
    total_bytes = 0
    chunk_size_bytes = CHUNK_SIZE_MB * 1024 * 1024
    while True:
        chunk_data = await file.read(chunk_size_bytes)

        if not chunk_data:
            if chunk_index == 0:
                await log(
                    entity_name=f"{file.filename}",
                    entity_type=EntityTypeEnum.FILE,
                    action=ActionTypeEnum.UPLOAD,
                    description="Файл пуст",
                    success=False,
                    session=session
                )
            break

        chunk_uuid = str(uuid.uuid4())

        await save_chunk_info(chunk_uuid, file_name, chunk_index, session)

        tasks = [
            upload_chunk_to_node(node, chunk_data, chunk_index, chunk_uuid, session)
            for node in target_nodes
        ]

        results = await asyncio.gather(*tasks)

        success_count = sum(1 for r in results if r is True)

        if success_count < RELEVANT_COUNT:
            await log(
                entity_name=f"{chunk_uuid}",
                entity_type=EntityTypeEnum.CHUNK,
                action=ActionTypeEnum.UPLOAD,
                description=f"Ошибка репликации блока. Успешно: {success_count}, Требуется: {RELEVANT_COUNT}",
                success=False,
                session=session
            )
            raise Exception(
                f"Ошибка репликации блока {chunk_index}. "
                f"Успешно: {success_count}, Требуется: {RELEVANT_COUNT}"
            )

        await make_chunk_active(chunk_uuid, session)
        total_bytes += len(chunk_data)
        chunk_index += 1
    return {
        "status": "complete",
        "total_chunks": chunk_index,
        "total_bytes": total_bytes
    }

# async def delete_useless_chunks(session: AsyncSession):
#     chunks = await get_useless_chunks(session)
#     chunk_and_storage = dict()
#     for chunk in chunks:
#         chunk_storage = await get_chunk_storage(chunk.id, session)
#         chunk_and_storage[chunk.id] = [cs.storage_id for cs in chunk_storage]
#
#     tasks = [
#         delete_chunks_from_node(chunks, node)
#         for node in target_nodes
#     ]
#     results = await asyncio.gather(*tasks)
#     if sum(results) < RELEVANT_COUNT:
#         raise Exception(f"Ошибка удаления блоков")
#     else:
#         print(f"Блоки файла {original_name} удалены с нод {target_nodes}")
#
#
# async def delete_chunks_from_node(chunk: str, node_url: str):
#     async with httpx.AsyncClient() as client:
#         for chunk in list_of_chunks:
#             response = await client.delete(f"http://{node_url}/api/file/{chunk.uuid}")
#             if response.status_code == 200:
#                 print(f"Блок {chunk_uuid} удален с ноды {node_url}")
#             else:
#                 print(f"Ошибка при удалении блока {chunk_uuid} с ноды {node_url}")
