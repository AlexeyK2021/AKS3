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
    size: Mapped[float] = mapped_column()
    md5sum: Mapped[str] = mapped_column()


class Chunk(Base):
    __tablename__ = "chunk"

    id: Mapped[str] = mapped_column(primary_key=True)
    file_id: Mapped[str] = mapped_column(ForeignKey("file.id"))


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

    async def save_file_info(self, sha256: str, filename: str, path: str, size: int):
        async with self.session_factory() as session:
            new_file = FileMetadata(sha256=sha256, filename=filename, path=path, size=size)
            session.add(new_file)
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
