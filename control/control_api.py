import os
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI

from control.controllers.database_controller import db_manager
from control.controllers.models import Base
from routers import buckets, nodes

load_dotenv()
API_PORT = int(os.getenv("API_PORT"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # await log(entity_name="DB", entity_type=EntityTypeEnum.SYSTEM, action= ActionTypeEnum.INITIALIZE, success=True, description="Initializing DB")

    # gc = GarbageCollector(db_manager.session_factory)
    # gc_task = asyncio.create_task(gc.run_forever())
    # log("API", "Garbage Collector запущен в фоновом режиме")

    yield

    print("API", "Остановка фоновых задач...")
    # gc_task.cancel()
    # try:
    #     await gc_task
    # except asyncio.CancelledError:
    #     log("API", "Garbage Collector успешно остановлен")

    await db_manager.engine.dispose()
    print("API", "Соединение с БД закрыто")


app = FastAPI(lifespan=lifespan, root_path="/api")
# app.include_router(files.router)
app.include_router(buckets.router)
app.include_router(nodes.router)
app.include_router(nodes.router)

if __name__ == "__main__":
    try:
        uvicorn.run(app, host="0.0.0.0", port=API_PORT, log_level="info")
    except KeyboardInterrupt:
        print("Shutting down API server")
