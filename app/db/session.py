from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# MongoDB client
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

mongodb_client = AsyncIOMotorClient(settings.MONGODB_URL)
mongodb_db = mongodb_client[settings.MONGODB_DB]

# Redis client
from redis import Redis
from app.core.config import settings

redis_client = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True
) 