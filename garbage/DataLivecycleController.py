import asyncio
import os
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv
from minio import Minio
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from DatabaseController import get_files_to_delete, get_filename_and_bucket, get_file_chunks_to_delete
from log import log
from models import File, Chunk, ChunkStorage, EntityTypeEnum, ActionTypeEnum

load_dotenv()
GARBAGE_COLLECTOR_PERIOD_SECS = float(os.getenv("GARBAGE_COLLECTOR_PERIOD_SECS", 30))
executor = ThreadPoolExecutor(max_workers=20)
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME")

class GarbageCollector:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def run_forever(self):
        print("GC", "Сборщик мусора запущен")
        while True:
            try:
                await self.cleanup_process()
            except Exception as e:
                print("GC", f"Критическая ошибка в цикле: {e}")
            await asyncio.sleep(GARBAGE_COLLECTOR_PERIOD_SECS)

    async def cleanup_process(self):
        async with self.session_factory() as session:
            file_ids = await get_files_to_delete(session)

            if not file_ids:
                return

            for f_id in file_ids:
                await self.delete_file_logic(f_id, session)

    async def delete_file_logic(self, file_id: int, session: AsyncSession):
        file_info = await get_filename_and_bucket(session, file_id)
        if not file_info:
            return

        filename, bucket_name = file_info
        locations = await get_file_chunks_to_delete(session, file_id)

        if not locations:
            return

        loop = asyncio.get_running_loop()
        tasks = []

        def minio_worker(ip, port, access, secret, obj_name):
            try:
                client = Minio(f"{ip}:{port}", access_key=access, secret_key=secret, secure=False)
                client.remove_object(MINIO_BUCKET_NAME, obj_name)
                return True
            except Exception as e:
                print(f"GC MinIO Error [{ip}:{port}]: {e}")
                return False

        for c_uuid, ip, port, access, secret in locations:
            tasks.append(
                loop.run_in_executor(executor, minio_worker, ip, port, access, secret, c_uuid)
            )

        results = await asyncio.gather(*tasks)
        bad_nodes = results.count(False)

        if bad_nodes == 0:
            try:
                chunk_ids_stmt = select(Chunk.id).where(Chunk.file_id == file_id)

                await session.execute(
                    delete(ChunkStorage).where(ChunkStorage.chunk_id.in_(chunk_ids_stmt))
                )
                await session.execute(
                    delete(Chunk).where(Chunk.file_id == file_id)
                )

                count_res = await session.execute(
                    select(func.count(Chunk.id)).where(Chunk.file_id == file_id)
                )
                remaining_chunks = count_res.scalar()

                if remaining_chunks == 0:
                    await session.execute(delete(File).where(File.id == file_id))
                    await log(
                        entity_name=f"{file_id}",
                        entity_type=EntityTypeEnum.FILE,
                        action=ActionTypeEnum.REMOVE,
                        description="Файл полностью стерт из системы",
                        success=True,
                        session=session
                    )
                    print("GC", f"Файл {filename} полностью стерт из системы.")
                else:
                    print("GC", f"Удалены блоки 'delete' файла {filename}. Осталось блоков: {remaining_chunks}")

                await session.commit()
            except Exception as e:
                await session.rollback()
                print("GC", f"Ошибка БД при очистке {filename}: {e}")
        else:
            print("GC", f"Пропуск очистки БД для {filename}: {bad_nodes} копий не удалено физически.")
