# Technical Architecture - Cricket Fitness Tracker

## Overview
This document outlines the technical architecture for the voice-powered cricket fitness tracker MVP, based on **FastAPI + HTMX** with real-time WebSocket communication for voice processing.

## Technology Stack Summary

### Core Framework
- **Backend**: FastAPI (Python 3.11+) with WebSocket support
- **Frontend**: HTMX with WebSocket extension
- **Templates**: Jinja2
- **WebSocket**: Starlette WebSocket (FastAPI's underlying layer)

### Voice & AI Pipeline
- **Speech-to-Text**: OpenAI Whisper API
- **LLM Processing**: OpenAI GPT-4 with **structured outputs** (latest 2024 syntax)
- **Voice Interface**: Real-time WebSocket streaming
- **Audio Processing**: Librosa for voice analysis

### Data Storage
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy 2.0 with async support
- **Migrations**: Alembic

## System Architecture

### High-Level Flow
```
User Voice Input → WebSocket → Audio Processing → Whisper STT → 
GPT-4 Structured Output → Database → Voice Confirmation → User
```

### Voice Processing Pipeline
```
1. Browser captures audio (Web Audio API)
2. Stream audio chunks via WebSocket 
3. Server buffers/processes with Librosa
4. Send to OpenAI Whisper for STT
5. Process text with GPT-4 (structured output)
6. Store in PostgreSQL via SQLAlchemy
7. Send confirmation back to user
```

## Detailed Implementation Patterns

### 1. OpenAI Integration (Latest 2024 Patterns)

#### Structured Output with Pydantic Models
```python
from openai import AsyncOpenAI
from pydantic import BaseModel
from typing import Literal, Optional

# Define structured output models
class FitnessEntry(BaseModel):
    type: Literal["running", "gym", "other"]
    duration_minutes: Optional[int] = None
    intensity: Literal["low", "medium", "high"]
    details: str
    mental_state: Literal["excellent", "good", "okay", "poor"]

class CricketCoachingEntry(BaseModel):
    activity: Literal["batting_drills", "wicket_keeping", "netting", "personal_coaching", "other"]
    what_went_well: str
    areas_for_improvement: str
    mental_state: Literal["excellent", "good", "okay", "poor"]

class RestDayEntry(BaseModel):
    activities: str
    recovery_quality: Literal["excellent", "good", "okay", "poor"]
    mental_state: Literal["excellent", "good", "okay", "poor"]

# Latest OpenAI API usage (2024)
async def process_voice_input(text: str, entry_type: str) -> dict:
    client = AsyncOpenAI(api_key="your-api-key")
    
    if entry_type == "fitness":
        completion = await client.beta.chat.completions.parse(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Extract fitness information from user voice input."},
                {"role": "user", "content": text}
            ],
            response_format=FitnessEntry,
        )
        return completion.choices[0].message.parsed
```

#### Whisper Integration
```python
async def transcribe_audio(audio_data: bytes) -> str:
    client = AsyncOpenAI()
    
    # Create temporary file for audio
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
        tmp_file.write(audio_data)
        tmp_file.flush()
        
        with open(tmp_file.name, "rb") as audio_file:
            transcript = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
    
    os.unlink(tmp_file.name)
    return transcript
```

### 2. FastAPI WebSocket Architecture (Current Best Practices)

#### WebSocket Connection Manager
```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
    
    async def send_personal_message(self, message: dict, session_id: str):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_text(json.dumps(message))

manager = ConnectionManager()

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    try:
        while True:
            # Receive audio data
            data = await websocket.receive_bytes()
            
            # Process audio with voice pipeline
            result = await process_voice_data(data)
            
            # Send back structured response
            await manager.send_personal_message({
                "type": "transcription",
                "data": result
            }, session_id)
            
    except WebSocketDisconnect:
        manager.disconnect(session_id)
```

#### Voice Data Processing
```python
import librosa
import numpy as np
from io import BytesIO

async def process_voice_data(audio_bytes: bytes) -> dict:
    try:
        # Convert bytes to audio using librosa
        audio_array, sample_rate = librosa.load(BytesIO(audio_bytes), sr=16000)
        
        # Voice Activity Detection
        intervals = librosa.effects.split(audio_array, top_db=20)
        
        if len(intervals) == 0:
            return {"error": "No speech detected"}
        
        # Extract speech segments
        speech_segments = []
        for interval in intervals:
            start, end = interval
            segment = audio_array[start:end]
            speech_segments.append(segment)
        
        # Combine segments and convert to bytes for Whisper
        combined_audio = np.concatenate(speech_segments)
        
        # Convert back to bytes for OpenAI
        import soundfile as sf
        buffer = BytesIO()
        sf.write(buffer, combined_audio, sample_rate, format='WAV')
        buffer.seek(0)
        
        # Transcribe with Whisper
        transcript = await transcribe_audio(buffer.read())
        
        return {
            "transcript": transcript,
            "confidence": "high",  # Could add actual confidence scoring
            "duration": len(combined_audio) / sample_rate
        }
        
    except Exception as e:
        return {"error": f"Processing failed: {str(e)}"}
```

### 3. Database Layer (SQLAlchemy 2.0 Async Patterns)

#### Database Models
```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, Text, Enum, ForeignKey
import datetime
import enum

class Base(DeclarativeBase):
    pass

class ActivityType(enum.Enum):
    FITNESS = "fitness"
    CRICKET_COACHING = "cricket_coaching"
    CRICKET_MATCH = "cricket_match"
    REST_DAY = "rest_day"

class Entry(Base):
    __tablename__ = "entries"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[datetime.date] = mapped_column(DateTime, default=datetime.date.today)
    activity_type: Mapped[ActivityType] = mapped_column(Enum(ActivityType))
    raw_transcript: Mapped[str] = mapped_column(Text)
    structured_data: Mapped[str] = mapped_column(Text)  # JSON stored as text
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

# Modern async database setup
DATABASE_URL = "postgresql+asyncpg://user:password@localhost/cricket_tracker"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
```

#### Database Operations
```python
from fastapi import Depends

async def save_entry(
    entry_data: dict, 
    session: AsyncSession = Depends(get_db)
) -> int:
    """Save a new entry to the database"""
    
    entry = Entry(
        activity_type=entry_data["type"],
        raw_transcript=entry_data["transcript"],
        structured_data=json.dumps(entry_data["structured"])
    )
    
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry.id

async def get_recent_entries(
    limit: int = 10,
    session: AsyncSession = Depends(get_db)
) -> List[Entry]:
    """Get recent entries for display"""
    
    result = await session.execute(
        select(Entry)
        .order_by(Entry.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()
```

### 4. Pydantic v2 Validation (Latest Patterns)

#### Advanced Validation Models
```python
from pydantic import BaseModel, Field, field_validator
from typing import Annotated, Optional, Literal
import re

class VoiceInputRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=100)
    audio_format: Literal["wav", "mp3", "webm"] = "wav"
    sample_rate: Annotated[int, Field(ge=8000, le=48000)] = 16000
    
    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Session ID must contain only alphanumeric characters, hyphens, and underscores')
        return v

class ProcessedEntry(BaseModel):
    entry_id: int
    confidence_score: Annotated[float, Field(ge=0.0, le=1.0)]
    processing_time_ms: int
    needs_clarification: bool = False
    clarification_questions: Optional[List[str]] = None
    
    @field_validator('confidence_score')
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        return round(v, 3)  # Round to 3 decimal places
```

### 5. Server Configuration (Uvicorn WebSocket Optimized)

#### Production Uvicorn Configuration
```python
# config/server.py
import uvicorn
from typing import Dict, Any

class UvicornConfig:
    """Production-ready Uvicorn configuration for voice processing"""
    
    @staticmethod
    def get_config() -> Dict[str, Any]:
        return {
            # Basic server settings
            "host": "0.0.0.0",
            "port": 8000,
            "workers": 1,  # Single worker for WebSocket state management
            
            # WebSocket optimizations
            "ws": "websockets",  # Use websockets library (best performance)
            "ws_max_size": 16777216,  # 16MB max message size for audio
            "ws_max_queue": 64,  # Increased queue for audio streaming
            "ws_ping_interval": 10.0,  # Keep connections alive
            "ws_ping_timeout": 5.0,
            "ws_per_message_deflate": False,  # Disable compression for audio
            
            # Performance settings
            "loop": "uvloop",  # Use uvloop for better performance
            "http": "httptools",  # Use httptools for HTTP parsing
            "backlog": 2048,
            
            # Timeouts
            "timeout_keep_alive": 30,  # Longer keep-alive for voice sessions
            "timeout_graceful_shutdown": 30,
            
            # Logging
            "log_level": "info",
            "access_log": True,
            
            # Limits
            "limit_concurrency": 100,  # Max concurrent connections
            "limit_max_requests": 10000,
        }

def run_server():
    config = UvicornConfig.get_config()
    uvicorn.run("main:app", **config)
```

### 6. Error Handling & Monitoring

#### Comprehensive Error Handling
```python
from fastapi import HTTPException, status
import logging
from typing import Union

logger = logging.getLogger(__name__)

class VoiceProcessingError(Exception):
    """Custom exception for voice processing errors"""
    pass

class DatabaseError(Exception):
    """Custom exception for database operations"""
    pass

@app.exception_handler(VoiceProcessingError)
async def voice_processing_exception_handler(request, exc):
    logger.error(f"Voice processing error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": "Voice processing failed", "error": str(exc)}
    )

@app.middleware("http")
async def error_handling_middleware(request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        logger.error(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
```

### 7. Security Considerations

#### WebSocket Security
```python
from fastapi import WebSocket, HTTPException, Depends
from fastapi.security import HTTPBearer
import jwt

security = HTTPBearer()

async def verify_websocket_token(websocket: WebSocket):
    """Verify JWT token for WebSocket connections"""
    
    # Get token from query params or headers
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return False
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get("user_id")
    except jwt.InvalidTokenError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return False

@app.websocket("/ws/{session_id}")
async def secure_websocket_endpoint(websocket: WebSocket, session_id: str):
    user_id = await verify_websocket_token(websocket)
    if not user_id:
        return
    
    await manager.connect(websocket, session_id, user_id)
    # ... rest of WebSocket handling
```

## Environment Configuration

### Development Environment
```python
# config/settings.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost/cricket_tracker"
    
    # OpenAI
    openai_api_key: str
    
    # Server
    debug: bool = True
    log_level: str = "debug"
    
    # Voice processing
    max_audio_duration: int = 300  # 5 minutes max
    supported_audio_formats: list = ["wav", "mp3", "webm"]
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### Production Environment
```python
# config/production.py
class ProductionSettings(Settings):
    debug: bool = False
    log_level: str = "info"
    
    # Production database with connection pooling
    database_url: str = "postgresql+asyncpg://user:password@prod-db:5432/cricket_tracker"
    database_pool_size: int = 20
    database_max_overflow: int = 0
    
    # Security
    secret_key: str
    cors_origins: list = ["https://crickettracker.app"]
    
    # Performance
    workers: int = 4
    limit_concurrency: int = 500
```

## Deployment Architecture

### Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run with uvicorn
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/cricket_tracker
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - db
      - redis
    volumes:
      - ./audio_temp:/app/audio_temp

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: cricket_tracker
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

## Performance Optimizations

### Audio Processing Optimizations
```python
# Async audio processing with background tasks
from fastapi import BackgroundTasks
import asyncio

async def process_audio_background(audio_data: bytes, session_id: str):
    """Process audio in background to avoid blocking WebSocket"""
    
    result = await process_voice_data(audio_data)
    
    # Send result back via WebSocket
    await manager.send_personal_message({
        "type": "processing_complete",
        "data": result
    }, session_id)

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            data = await websocket.receive_bytes()
            
            # Process audio in background
            asyncio.create_task(
                process_audio_background(data, session_id)
            )
            
            # Immediately acknowledge receipt
            await manager.send_personal_message({
                "type": "audio_received",
                "status": "processing"
            }, session_id)
            
    except WebSocketDisconnect:
        manager.disconnect(session_id)
```

## Next Steps

1. **Initialize Project Structure**: Set up FastAPI project with all dependencies
2. **Implement Core WebSocket**: Basic voice streaming functionality  
3. **OpenAI Integration**: Whisper + GPT-4 structured outputs
4. **Database Setup**: PostgreSQL with SQLAlchemy 2.0 async
5. **HTMX Frontend**: Voice recording interface
6. **Testing**: Voice processing pipeline testing
7. **Deployment**: Docker + production configuration

This architecture provides a solid foundation for a production-ready voice-powered cricket fitness tracker with modern Python async patterns and real-time capabilities. 