# database/models.py
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    ForeignKey,
    Enum,
    DateTime,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from config import DATABASE_URL
import enum
from datetime import datetime, timedelta

Base = declarative_base()


class SummaryFrequency(enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    chat_id = Column(String, unique=True, nullable=False)
    mailboxes = relationship("Mailbox", back_populates="user")


class Mailbox(Base):
    __tablename__ = "mailboxes"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    tag = Column(String)
    summary_frequency = Column(Enum(SummaryFrequency), default=SummaryFrequency.DAILY)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="mailboxes")
    password = Column(String, nullable=False)  # Encrypt this later
    last_summary_sent = Column(DateTime, default=datetime.utcnow)
    next_summary_time = Column(DateTime, default=datetime.utcnow)

    def calculate_next_summary_time(self):
        if self.summary_frequency == SummaryFrequency.DAILY:
            self.next_summary_time = datetime.utcnow() + timedelta(days=1)
        elif self.summary_frequency == SummaryFrequency.WEEKLY:
            self.next_summary_time = datetime.utcnow() + timedelta(days=7)


# Create the database engine
engine = create_engine(DATABASE_URL)

# Create all tables
Base.metadata.create_all(engine)

# Create a session factory
Session = sessionmaker(bind=engine)


def get_session():
    return Session()
