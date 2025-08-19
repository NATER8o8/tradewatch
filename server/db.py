
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import env

DATABASE_URL = env("DATABASE_URL", "sqlite:///./otp.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
