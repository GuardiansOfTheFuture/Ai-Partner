"""SQLAlchemy 异步引擎"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.config import settings

engine = create_async_engine(settings.mysql_url, echo=False, pool_size=5)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
