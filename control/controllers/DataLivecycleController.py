import asyncio
import os

import httpx
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession

from control.controllers.DatabaseController import get_files_to_delete, get_chunks_of_file, delete_file_info
from control.controllers.models import FileStatusEnum
from control.log import log

load_dotenv()
GARBAGE_COLLECTOR_PERIOD_SECS = float(os.getenv("GARBAGE_COLLECTOR_PERIOD_SECS"))


class GarbageCollector:
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.status_delete_id = FileStatusEnum.DELETE

    async def run_forever(self):
        while True:
            try:
                await self.cleanup_orphaned_files()
            except Exception as e:
                log("GC", f"Ошибка в работе: {e}")

            await asyncio.sleep(GARBAGE_COLLECTOR_PERIOD_SECS)

    async def cleanup_orphaned_files(self):
        async with self.session_factory() as session:
            files_to_delete = await get_files_to_delete(session)

            if not files_to_delete:
                return

            log("GC", f"Найдено {len(files_to_delete)} файлов для удаления.")

            for file in files_to_delete:
                log("GC", f"Удаление файла {file.filename}")
                await self.delete_file_completely(file, session)

    async def delete_file_completely(self, file, session: AsyncSession):
        locations = await get_chunks_of_file(session, file.id)

        async with httpx.AsyncClient() as client:
            tasks = []
            for chunk_id, ip, port in locations:
                url = f"http://{ip}:{port}/api/file/{chunk_id}"
                tasks.append(client.delete(url, timeout=2.0))

            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)

            bad = 0
            for r in results:
                if isinstance(r, Exception):
                    bad += 1

            log("GC", f"Отправлено {len(tasks)} команд на удаление для файла {file.filename}")
            log("GC", f"Неуспешно выполнено {bad} команд на удаление для файла {file.filename}")

            if bad == 0:
                await delete_file_info(session, file.id)

                await session.commit()
                log("GC", f"Файл {file.filename} полностью удален из системы.")
            else:
                log("GC", f"Файл {file.filename} удален только с некоторых нод")
