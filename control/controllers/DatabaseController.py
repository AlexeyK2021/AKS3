import os
from typing import List

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from control.controllers.models import Base, FileMetadata, Chunk, ChunkStorage, Storage


async def commit_session(session: AsyncSession):
    await session.commit()


async def rollback_session(session: AsyncSession):
    await session.rollback()


async def save_file_info(filename: str, session: AsyncSession):
    new_file = FileMetadata(filename=filename)
    session.add(new_file)
    await session.flush()
    # await session.commit()


async def save_chunk_info(chunk_id: str, file_name: str, chunk_index: int, session: AsyncSession):
    file = (await session.execute(
        select(FileMetadata)
        .where(FileMetadata.filename == file_name)
    )).scalars().all()[0]
    new_chunk = Chunk(id=chunk_id, file_id=file.id, chunk_index=chunk_index)
    session.add(new_chunk)
    await session.flush()
    # await session.commit()


async def save_chunk_storage_info(chunk_id: str, storage_url: str, session: AsyncSession):
    ip, port = storage_url.split(":")
    storage = (await session.execute(
        select(Storage)
        .where(Storage.ip == ip, Storage.port == port)
    )).scalars().all()[0]
    new_chunk_storage = ChunkStorage(storage_id=storage.id, chunk_id=chunk_id)
    session.add(new_chunk_storage)
    await session.flush()
    # await session.commit()


async def get_chunks_by_file(filename: str, session: AsyncSession):
    result = (await session.execute(
        select(Chunk)
        .join(FileMetadata, Chunk.file_id == FileMetadata.id)
        .where(FileMetadata.filename == filename)
    )).scalars().all()
    return result


class DatabaseController:
    def __init__(self, db_url: str):
        # db_url может быть:
        # "sqlite+aiosqlite:///./test.db"
        # или "postgresql+asyncpg://user:pass@localhost/dbname"
        self.engine = create_async_engine(db_url, echo=True)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def create_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_session(self):
        return self.session_factory()

    async def close_session(self):
        await self.engine.dispose()

    async def get_storages(self):
        async with self.session_factory() as session:
            result = await session.execute(select(Storage))
            return result.scalars().all()


load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./local.db")
db_manager = DatabaseController(DATABASE_URL)


async def get_db():
    async with db_manager.session_factory() as session:
        yield session
