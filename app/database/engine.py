from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os 


DATABASE_URL = os.getenv("DATABASE_URL")


engine = create_engine.create(
    DATABASE_URL,
    pool_pre_pine = True
)

SessionLocal = sessionmaker(
    bind = engine,
    autoflush=False,
    autocommit = False
)
