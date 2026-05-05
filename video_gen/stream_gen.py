# import asyncio
# import httpx
# import time
# import io
# import subprocess
#
#
# class ProcessReader(io.RawIOBase):
#
#     def __init__(self, process):
#         self.process = process
#         self.stdout = process.stdout
#
#     def readable(self):
#         return True
#
#     def readinto(self, b):
#         # Читаем данные напрямую из stdout процесса в буфер библиотеки httpx
#         data = self.stdout.read(len(b))
#         if not data:
#             return 0
#         n = len(data)
#         b[:n] = data
#         return n
#
#
# async def camera_video_emulator(target_url, duration_secs, filename):
#     ffmpeg_cmd = [
#         '.\\ffmpeg.exe',
#         '-re',
#         '-f', 'lavfi',
#         '-i', 'testsrc=size=1920x1080:rate=60',  # Тестовая таблица
#         '-t', str(duration_secs),  # Длительность в секундах
#         '-f', 'matroska',  # Формат контейнера
#         '-vcodec', 'libx264',  # Кодек
#         '-preset', 'ultrafast',  # Минимальная нагрузка на CPU
#         'pipe:1'  # Вывод в stdout
#     ]
#
#     print(f"Запуск генерации видео ({duration_secs} сек)...")
#     process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, bufsize=10 ** 6)
#
#     # Оборачиваем процесс в наш адаптер
#     payload = ProcessReader(process)
#
#     start_time = time.time()
#     async with httpx.AsyncClient(timeout=None) as client:
#         files = {
#             "file": (filename, payload, "video/x-matroska")
#         }
#
#         try:
#             response = await client.post(target_url, files=files)
#
#             duration = time.time() - start_time
#             print(f"Статус: {response.status_code}")
#             print(f"Ответ: {response.json()}")
#             print(f"Загрузка завершена за {duration:.2f} сек.")
#         except Exception as e:
#             print(f"Ошибка: {e}")
#         finally:
#             process.terminate()
#
#
# if __name__ == "__main__":
#     # URL твоего контроллера
#     URL = "http://192.168.88.2:5051/api/file/8"
#     asyncio.run(camera_video_emulator(URL, 100, "camera_live_test3.mkv"))

import asyncio
import httpx
import time
import io
import os
import subprocess


# ==========================================
# 1. АДАПТЕР ДЛЯ ПОТОКОВОЙ ПЕРЕДАЧИ
# ==========================================
class FileStreamReader(io.RawIOBase):
    """
    Адаптер, который позволяет httpx читать файл с диска
    порциями (стримить), не загружая его целиком в ОЗУ.
    """

    def __init__(self, file_object):
        self.file_object = file_object

    def readable(self):
        return True

    def readinto(self, b):
        data = self.file_object.read(len(b))
        if not data:
            return 0
        n = len(data)
        b[:n] = data
        return n


# ==========================================
# 2. ФУНКЦИЯ ГЕНЕРАЦИИ ВИДЕО НА ДИСК
# ==========================================
def generate_test_video(output_path: str, duration_secs: int = 10):
    """
    Генерирует тестовое видео с таймером и сохраняет его на локальный диск.
    """
    print(f"Генерация тестового видео ({duration_secs} сек) в файл: {output_path}...")

    ffmpeg_cmd = [
        'ffmpeg',
        '-y',  # Перезаписывать файл, если он существует
        '-f', 'lavfi',
        '-i', f'testsrc=size=1280x720:rate=30',  # Тестовая таблица с таймером
        '-t', str(duration_secs),
        '-vcodec', 'libx264',
        '-preset', 'ultrafast',
        output_path
    ]

    # Запускаем и ждем окончания генерации
    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    process.wait()
    print("Генерация успешно завершена.")


# ==========================================
# 3. ФУНКЦИЯ ОТПРАВКИ ФАЙЛА НА API
# ==========================================
async def send_file_to_api(target_url: str, file_path: str, remote_filename: str):
    """
    Отправляет любой локальный файл на указанный URL в формате Multipart (UploadFile).
    Передача идет в потоковом режиме, безопасном для ОЗУ.
    """
    if not os.path.exists(file_path):
        print(f"Ошибка: Локальный файл {file_path} не найден!")
        return

    # Определяем MIME-тип (по умолчанию октет-стрим)
    content_type = "application/octet-stream"
    if file_path.endswith('.mp4'):
        content_type = "video/mp4"
    elif file_path.endswith('.mkv'):
        content_type = "video/x-matroska"

    print(f"Начало отправки файла '{file_path}' на {target_url}...")
    start_time = time.time()

    # Открываем файл и оборачиваем в адаптер
    with open(file_path, 'rb') as f:
        payload = FileStreamReader(f)

        async with httpx.AsyncClient(timeout=None) as client:
            files = {
                "file": (remote_filename, payload, content_type)
            }
            try:
                response = await client.post(target_url, files=files)
                duration = time.time() - start_time

                print(f"Статус ответа: {response.status_code}")
                print(f"Ответ API: {response.json()}")
                print(f"Отправка завершена за {duration:.2f} сек.")
            except Exception as e:
                print(f"Ошибка при отправке: {e}")


# ==========================================
# ПРИМЕР ИСПОЛЬЗОВАНИЯ
# ==========================================
if __name__ == "__main__":
    API_URL = "http://192.168.88.2:5051/api/file/8"
    LOCAL_VIDEO_PATH = "test_video.mp4"

    # Сценарий использования:
    # 1. Генерируем тестовое видео локально
    # generate_test_video(output_path=LOCAL_VIDEO_PATH, duration_secs=15)

    # 2. Отправляем его (или любой другой твой файл, просто замени путь)
    asyncio.run(send_file_to_api(
        target_url=API_URL,
        file_path=LOCAL_VIDEO_PATH,  # Путь к локальному файлу
        remote_filename=LOCAL_VIDEO_PATH  # Имя, под которым файл запишется в систему
    ))

    # (Опционально) удаляем временный файл после отправки
    # if os.path.exists(LOCAL_VIDEO_PATH):
    #     os.remove(LOCAL_VIDEO_PATH)