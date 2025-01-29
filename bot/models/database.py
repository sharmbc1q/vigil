from sqlalchemy import create_engine, Column, Integer, String, Text, BigInteger, DateTime, func, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings
from datetime import datetime

# Database setup
DATABASE_URL = settings.DATABASE_URL  # Use environment variable to provide DB URL
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# Short-Term Memory Model
class ShortTermMemory(Base):
    __tablename__ = "short_term_memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, index=True, nullable=False)
    user_message = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=False)
    creation_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expiration_time = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index('idx_short_term_expiration', 'expiration_time'),
    )


# Long-Term Memory Model
class LongTermMemory(Base):
    __tablename__ = "long_term_memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, index=True, nullable=False)
    server_id = Column(BigInteger, index=True, nullable=True)
    type = Column(String(50), nullable=False)  # e.g., "preference", "fact"
    content = Column(Text, nullable=False)
    importance = Column(Integer, default=1, nullable=False)  # Importance level (1 to 5)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_user_server', 'user_id', 'server_id'),
    )


# Create tables in the database
def initialize_database():
    Base.metadata.create_all(bind=engine)