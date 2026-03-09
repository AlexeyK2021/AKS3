import os
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI

from control.controllers.models import Base
from control.routers import buckets
from controllers.DatabaseController import db_manager
from control.routers import files

load_dotenv()
API_PORT = int(os.getenv("API_PORT"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("База данных инициализирована")

    yield

    await db_manager.engine.dispose()
    print("Соединение с БД закрыто")


app = FastAPI(lifespan=lifespan, root_path="/api")
app.include_router(files.router)
app.include_router(buckets.router)

if __name__ == "__main__":
    try:
        uvicorn.run(app, host="0.0.0.0", port=API_PORT, log_level="info")
    except KeyboardInterrupt:
        print("Shutting down API server")
