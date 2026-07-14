from sqlalchemy import Column, Integer, String, Text, DateTime
import datetime
from database import Base
import os


class ChatMessage(Base):

    __tablename__ = "chat_messages"
    id=Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True)
    sender = Column(String(50))
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class CalendarEvent(Base):
    __tablename__ = "calendar_events"
    id=Column(Integer,primary_key=True, index=True )
    title = Column(String(200))
    description = Column(Text , nullable=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)