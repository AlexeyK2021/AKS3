import asyncio
import os
import uuid

import httpx
from dotenv import load_dotenv
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from control.controllers.DatabaseController import db_manager, save_chunk_info, save_chunk_storage_info, get_storages

load_dotenv()
PATH = os.getenv("DATA_PATH")
RELEVANT_COUNT = int(os.getenv("RELEVANT_COUNT"))
RELEVANT_CPU_PRIORITY = float(os.getenv("RELEVANT_CPU_PRIORITY"))
RELEVANT_RAM_PRIORITY = float(os.getenv("RELEVANT_RAM_PRIORITY"))
RELEVANT_DISK_PRIORITY = float(os.getenv("RELEVANT_DISK_PRIORITY"))
CHUNK_SIZE_MB = int(os.getenv("CHUNK_SIZE_MB"))


async def find_online_nodes(session: AsyncSession) -> dict[str, list[float]]:
    storages = await get_storages(session)
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
                               chunk_index: int, chunk_uuid: str, session: AsyncSession) -> bool:
    try:
        response = await client.post(f"http://{node_url}/api/file/{chunk_uuid}", content=chunk_data, timeout=60.0)
        if response.status_code == 200:
            print(f"Блок {chunk_uuid}({chunk_index}) загружен на ноду {node_url}")
            await save_chunk_storage_info(chunk_uuid, node_url, session)
            return True
        else:
            print(f"Нода {node_url} ответила ошибкой {response.status_code}")
            return False
    except Exception as e:
        print(f"Ошибка при отправке блока {chunk_index} на {node_url}: {e}")
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

    async with httpx.AsyncClient() as client:
        while True:
            chunk_data = await file.read(chunk_size_bytes)

            if not chunk_data:
                if chunk_index == 0:
                    print("Предупреждение: Файл пуст")
                break

            chunk_uuid = str(uuid.uuid4())

            await save_chunk_info(chunk_uuid, file_name, chunk_index, session)

            tasks = [
                upload_chunk_to_node(client, node, chunk_data, chunk_index, chunk_uuid, session)
                for node in target_nodes
            ]

            results = await asyncio.gather(*tasks)

            success_count = sum(1 for r in results if r is True)

            if success_count < RELEVANT_COUNT:
                raise Exception(
                    f"Ошибка репликации блока {chunk_index}. "
                    f"Успешно: {success_count}, Требуется: {RELEVANT_COUNT}"
                )

            total_bytes += len(chunk_data)
            print(f"Блок {chunk_index} ({len(chunk_data)} байт) записан на {success_count} нод.")

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