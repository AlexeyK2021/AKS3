from sqlalchemy.ext.asyncio import AsyncSession

from write.controllers.database_controller import db_manager, write_log, commit_session


async def log(entity_name, entity_type: int, action: int, description: str, success: bool, session: AsyncSession):
    session = await db_manager.get_session()

    await write_log(entity_name, entity_type, action, description, success, session)
    await commit_session(session)
    await session.close()