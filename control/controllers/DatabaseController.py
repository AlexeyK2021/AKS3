import os

from dotenv import load_dotenv
from sqlalchemy import select, delete, insert, update
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from control.controllers.models import Base, File, Chunk, ChunkStorage, Storage, FileStatus, Bucket, FileStatusEnum


async def commit_session(session: AsyncSession):
    await session.commit()


async def rollback_session(session: AsyncSession):
    await session.rollback()


async def add_file_info(new_file: File, session: AsyncSession):
    # new_file = FileMetadata(filename=filename, status_id=status_id)
    session.add(new_file)
    await session.flush()
    # await session.commit()


async def save_chunk_info(chunk_id: str, file_name: str, chunk_index: int, session: AsyncSession):
    file = (await session.execute(
        select(File)
        .where(File.filename == file_name)
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
    # await session.flush()
    # await session.commit()


async def get_useless_chunks(session: AsyncSession):
    result = (await session.execute(
        select(Chunk)
        .join(File, Chunk.file_id == File.id)
        .join(FileStatus, File.status_id == FileStatus.id)
        .where(FileStatus.name == "error")
    )).scalars().all()
    return result


async def get_chunk_storage(chunk_id: str, session: AsyncSession):
    return (await session.execute(
        select(ChunkStorage)
        .where(ChunkStorage.chunk_id == chunk_id)
    )).scalars().all()


async def get_files_by_bucket(bucket_id: int, session: AsyncSession):
    return (await session.execute(
        select(File)
        .where(File.bucket_id == bucket_id, File.status_id == FileStatusEnum.ACTIVE)
    )).scalars().all()


async def get_file_in_bucket(bucket_id: int, file_id: str, session: AsyncSession):
    return (await session.execute(
        select(File)
        .where(File.bucket_id == bucket_id, File.id == file_id)
    )).scalars().first()


async def create_bucket(bucket_name: str, session: AsyncSession):
    new_bucket = Bucket(name=bucket_name)
    # bucket_id = await session.execute(
    #     insert(Bucket)
    #     .values()
    #     .returning(Bucket.id)
    # )
    session.add(new_bucket)
    await session.flush()


async def get_buckets_list(session: AsyncSession):
    results = await session.execute(select(Bucket))
    return results.scalars().all()


async def delete_bucket(bucket_id: int, session: AsyncSession):
    return await session.execute(
        delete(Bucket)
        .where(Bucket.id == bucket_id)
        .returning(Bucket.id)
    )


async def get_storages(session: AsyncSession):
    result = await session.execute(select(Storage))
    return result.scalars().all()


class DatabaseController:
    def __init__(self, db_url: str):
        self.engine = create_async_engine(db_url, echo=True)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def create_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_session(self):
        return self.session_factory()

    async def close_session(self):
        await self.engine.dispose()


load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./local.db")
db_manager = DatabaseController(DATABASE_URL)


async def get_db():
    async with db_manager.session_factory() as session:
        yield session
