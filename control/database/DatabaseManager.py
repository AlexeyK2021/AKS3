import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class FileMetadata(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True)
    sha256: Mapped[str] = mapped_column(unique=True, index=True)
    filename: Mapped[str] = mapped_column()
    path: Mapped[str] = mapped_column()
    size: Mapped[float] = mapped_column()


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


load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./local.db")
db_manager = DatabaseManager(DATABASE_URL)


async def get_db():
    async with db_manager.session_factory() as session:
        yield session
