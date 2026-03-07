import os

from dotenv import load_dotenv
from sqlalchemy import ForeignKey, select, Connection
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class FileMetadata(Base):
    __tablename__ = "file"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column()
    # size: Mapped[float] = mapped_column(nullable=True)
    # md5sum: Mapped[str] = mapped_column()


class Chunk(Base):
    __tablename__ = "chunk"

    id: Mapped[str] = mapped_column(primary_key=True)
    file_id: Mapped[int] = mapped_column(ForeignKey("file.id"))
    chunk_index: Mapped[int] = mapped_column()


class ChunkStorage(Base):
    __tablename__ = "chunk_storage"

    id: Mapped[int] = mapped_column(primary_key=True)
    storage_id: Mapped[int] = mapped_column(ForeignKey("storage.id"))
    chunk_id: Mapped[str] = mapped_column(ForeignKey("chunk.id"))


class Storage(Base):
    __tablename__ = "storage"

    id: Mapped[int] = mapped_column(primary_key=True)
    ip: Mapped[str] = mapped_column()
    port: Mapped[str] = mapped_column()


class DatabaseManager:
    def __init__(self, db_url: str):
        # db_url может быть:
        # "sqlite+aiosqlite:///./test.db"
        # или "postgresql+asyncpg://user:pass@localhost/dbname"
        self.engine = create_async_engine(db_url, echo=True)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def create_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def save_file_info(self, filename: str):
        async with self.session_factory() as session:
            new_file = FileMetadata(filename=filename)
            session.add(new_file)
            await session.commit()

    async def save_chunk_info(self, chunk_id: str, file_name: str, chunk_index: int):
        async with self.session_factory() as session:
            file = (await session.execute(select(FileMetadata).where(FileMetadata.filename == file_name))).scalars().all()[0]
            new_chunk = Chunk(id=chunk_id, file_id=file.id, chunk_index=chunk_index)
            session.add(new_chunk)
            await session.commit()

    async def save_chunk_storage_info(self, chunk_id: str, storage_url: str):
        async with self.session_factory() as session:
            ip, port = storage_url.split(":")
            storage = (await session.execute(select(Storage).where(Storage.ip == ip, Storage.port == port))).scalars().all()[0]
            new_chunk_storage = ChunkStorage(storage_id=storage.id, chunk_id=chunk_id)
            session.add(new_chunk_storage)
            await session.commit()

    async def get_storages(self):
        async with self.session_factory() as session:
            result = await session.execute(select(Storage))
            return result.scalars().all()


load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./local.db")
db_manager = DatabaseManager(DATABASE_URL)


async def get_db():
    async with db_manager.session_factory() as session:
        yield session
