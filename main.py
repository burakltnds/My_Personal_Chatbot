from fastapi import FastAPI,Depends,HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ai_service import get_gemini_response
import models
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Chatbot API", version="1.0.0")

#pydentic şemaları

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    id: int
    session_id: str
    sender: str
    message: str
    
    class Config:
        from_attributes = True

class EventCreate(BaseModel):
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime

class EventResponse(BaseModel):
    id: int 
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    class Config:
        from_attributes= True
            
    

@app.get("/")
def read_root():
    return {"status":"ok" , "message":"Sistem Ayakta"}

@app.post("/chat" , response_model= ChatResponse)
def send_message(request: ChatRequest, db: Session = Depends(get_db)):
    
    user_message = models.ChatMessage(
        session_id=request.session_id,
        sender="user",
        message=request.message
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    bot_reply_text = get_gemini_response(request.message, db)

    bot_message = models.ChatMessage(
        session_id=request.session_id,
        sender="asistan",
        message=bot_reply_text
    )
    db.add(bot_message)
    db.commit()
    db.refresh(bot_message)

    return bot_message

@app.post("/calendar", response_model=EventResponse)
def CreateEvent(event: EventCreate , db: Session = Depends(get_db)):
    new_event = models.CalendarEvent(
        title=event.title,
        description=event.description,
        start_time=event.start_time,
        end_time=event.end_time
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return new_event

@app.get("/calendar", response_model=List[EventResponse])
def get_events(db: Session = Depends(get_db)):
    events = db.query(models.CalendarEvent).order_by(models.CalendarEvent.start_time.asc()).all()
    return events

@app.get("/chat/history/{session_id}" , response_model=List[ChatResponse])
def get_chat_history(session_id: str, db: Session = Depends(get_db)):

    history = db.query(models.ChatMessage)\
        .filter(models.ChatMessage.session_id == session_id)\
            .order_by(models.ChatMessage.timestamp.asc())\
                .all()
    if not history:
        raise HTTPException(status_code=404, detail="Bu oturuma ait geçmiş bulunamadı")
    
    return history