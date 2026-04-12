# import asyncio
# import httpx
# import time
# import io
#
#
# class GeneratorToReader(io.RawIOBase):
#     """Адаптер, который превращает генератор в объект с методом .read()"""
#
#     def __init__(self, generator):
#         self.gen = generator
#         self.leftover = b""
#
#     def readable(self):
#         return True
#
#     def readinto(self, b):
#         try:
#             chunk = self.leftover or next(self.gen)
#         except StopIteration:
#             return 0  # Конец "файла"
#
#         n = len(chunk)
#         dest_len = len(b)
#
#         if n <= dest_len:
#             b[:n] = chunk
#             self.leftover = b""
#             return n
#         else:
#             b[:] = chunk[:dest_len]
#             self.leftover = chunk[dest_len:]
#             return dest_len
#
#
# async def camera_upload_emulator(target_url, file_size_mb, filename):
#     total_bytes = file_size_mb * 1024 * 1024
#
#     # Сам генератор байтов
#     def file_payload_generator():
#         bytes_sent = 0
#         chunk_size = 256 * 1024  # 256 КБ — оптимально для буфера
#         while bytes_sent < total_bytes:
#             remaining = total_bytes - bytes_sent
#             current_chunk_size = min(chunk_size, remaining)
#             # Генерируем блок данных (нули)
#             yield b"\0" * current_chunk_size
#             bytes_sent += current_chunk_size
#
#     print(f"Начинаю загрузку {file_size_mb} МБ через UploadFile (Multipart)...")
#     start_time = time.time()
#
#     # Оборачиваем генератор в адаптер, который понимает httpx
#     payload = GeneratorToReader(file_payload_generator())
#
#     async with httpx.AsyncClient(timeout=None) as client:
#         # Теперь httpx сможет вызывать .read() у нашего объекта
#         files = {
#             "file": (filename, payload, "application/octet-stream")
#         }
#
#         try:
#             response = await client.post(target_url, files=files)
#
#             duration = time.time() - start_time
#             print(f"Статус: {response.status_code}")
#             print(f"Ответ: {response.json()}")
#             print(f"Время выполнения: {duration:.2f} сек.")
#             print(f"Средняя скорость: {(file_size_mb / duration):.2f} МБ/с")
#         except Exception as e:
#             print(f"Ошибка при отправке: {e}")
#
#
# if __name__ == "__main__":
#     URL = "http://192.168.88.2:5051/api/file/8"
#     asyncio.run(camera_upload_emulator(URL, 1000, "large_camera_dump.mkv"))

import asyncio
import httpx
import time
import io
import subprocess


class ProcessReader(io.RawIOBase):
    """Адаптер, который читает stdout процесса как обычный файл"""

    def __init__(self, process):
        self.process = process
        self.stdout = process.stdout

    def readable(self):
        return True

    def readinto(self, b):
        # Читаем данные напрямую из stdout процесса в буфер библиотеки httpx
        data = self.stdout.read(len(b))
        if not data:
            return 0
        n = len(data)
        b[:n] = data
        return n


async def camera_video_emulator(target_url, duration_secs, filename):
    ffmpeg_cmd = [
        '.\\ffmpeg.exe',
        '-re',
        '-f', 'lavfi',
        '-i', 'testsrc=size=1920x1080:rate=60',  # Тестовая таблица
        '-t', str(duration_secs),  # Длительность в секундах
        '-f', 'matroska',  # Формат контейнера
        '-vcodec', 'libx264',  # Кодек
        '-preset', 'ultrafast',  # Минимальная нагрузка на CPU
        'pipe:1'  # Вывод в stdout
    ]

    print(f"Запуск генерации видео ({duration_secs} сек)...")
    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, bufsize=10 ** 6)

    # Оборачиваем процесс в наш адаптер
    payload = ProcessReader(process)

    start_time = time.time()
    async with httpx.AsyncClient(timeout=None) as client:
        files = {
            "file": (filename, payload, "video/x-matroska")
        }

        try:
            response = await client.post(target_url, files=files)

            duration = time.time() - start_time
            print(f"Статус: {response.status_code}")
            print(f"Ответ: {response.json()}")
            print(f"Загрузка завершена за {duration:.2f} сек.")
        except Exception as e:
            print(f"Ошибка: {e}")
        finally:
            process.terminate()


if __name__ == "__main__":
    # URL твоего контроллера
    URL = "http://192.168.88.2:5051/api/file/8"
    asyncio.run(camera_video_emulator(URL, 100, "camera_live_test3.mkv"))