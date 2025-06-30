# 🏏 Cricket Fitness Tracker

**Latest 2025 Update**: Now featuring modern async patterns, enhanced voice processing, and production-ready architecture!

A comprehensive voice-powered fitness and cricket activity tracking system designed specifically for young athletes. Built with the latest 2025 FastAPI patterns, async SQLAlchemy, and modern AI voice processing.

## ✨ Key Features

### 🎯 **Voice-First Interface**
- Real-time voice recording and processing
- AI-powered structured data extraction using OpenAI's latest structured outputs
- Support for multiple activity types with specialized prompts

### 🏏 **Cricket-Specific Tracking**
- **Fitness Activities**: Running, gym workouts, strength training
- **Cricket Coaching**: Practice sessions, drills, technique development
- **Match Performance**: Batting stats, wicket-keeping, bowling analysis
- **Rest & Recovery**: Sleep tracking, wellness monitoring

### 🚀 **Modern 2025 Architecture**
- **FastAPI**: Latest async patterns with modern lifespan management
- **SQLAlchemy 2.0**: Production-ready async database operations with connection pooling
- **OpenAI Integration**: Latest `client.beta.chat.completions.parse()` with Pydantic models
- **WebSocket Streaming**: Optimized real-time voice processing with connection management
- **Docker**: Production-ready containerization with health checks

## 🏃‍♂️ Quick Start

### Prerequisites
- Docker and Docker Compose
- OpenAI API key

### 1. Setup Environment
```bash
# Set your OpenAI API key
export OPENAI_API_KEY="your-openai-api-key-here"
```

### 2. Start the System
```bash
# Start everything with Docker Compose (recommended)
docker compose up -d

# The system will be available at:
# - Web Interface: http://localhost:8020
# - API Documentation: http://localhost:8020/api/docs
# - Health Check: http://localhost:8020/health
```

### 3. Using the Voice Interface
1. Open http://localhost:8020 in your browser
2. Select an activity type (Fitness, Cricket Coaching, Match, or Rest Day)
3. Click the record button and speak about your activity
4. View the AI-processed structured data in real-time

## 🏗️ System Architecture

### **Latest 2025 Patterns Implemented**

#### **Database Layer** 
- **SQLAlchemy 2.0 Async**: Modern `async_sessionmaker` with connection pooling
- **Production Optimization**: 20 concurrent connections, 30 overflow, 1-hour recycle
- **Health Monitoring**: Real-time connection statistics and monitoring

#### **API Layer**
- **FastAPI Modern Lifespan**: Proper startup/shutdown resource management
- **WebSocket Optimization**: Real-time voice streaming with error recovery
- **Static File Serving**: Integrated HTML interface with responsive design

#### **AI Processing**
- **OpenAI Structured Outputs**: Latest `client.beta.chat.completions.parse()` API
- **Cricket-Specific Prompts**: Specialized AI prompting for cricket analytics
- **Robust Error Handling**: Fallback mechanisms and retry logic

## 🧪 Testing & Quality

Comprehensive test suite with 100% passing rate:

```bash
# Run all tests (52 tests passing)
docker compose exec web pytest

# Run with coverage report
docker compose exec web pytest --cov=app --cov-report=html

# Test categories:
# - 15 database model tests
# - 19 Pydantic validation tests  
# - 18 WebSocket and voice processing tests
```

## 📊 API Endpoints

### **Web Interface**
- `GET /` - Modern responsive web interface
- `GET /health` - Comprehensive system health check

### **Session Management**
- `POST /api/sessions` - Create new voice session with UUID
- `GET /api/sessions/{session_id}` - Get session status and connection info

### **Real-time Processing**
- `WS /ws/voice/{session_id}` - WebSocket for voice data streaming
- Supports both text commands (ping/pong) and binary audio data

## 🔧 Development

### **Local Development**
```bash
# Install dependencies with Poetry
poetry install

# Set up environment
export OPENAI_API_KEY="your-key"
export DATABASE_URL="postgresql+asyncpg://user:password@localhost:9432/cricket_fitness"

# Run development server
poetry run uvicorn app.main:app --reload --port 8010
```

### **Development Features**
- Live reloading with volume mounts
- Comprehensive logging with structured output
- Debug mode with detailed error traces
- Interactive API documentation

## 🎯 2025 Technical Improvements

### **Performance Enhancements**
- **Async Everything**: Full async pipeline from WebSocket to database
- **Connection Pooling**: Optimized database connections for high concurrency
- **Voice Processing**: Non-blocking audio processing with Librosa VAD

### **Production Readiness**
- **Health Monitoring**: Database, WebSocket, and system health endpoints
- **Error Handling**: Production-grade exception handling and recovery
- **Security**: CORS configuration and input validation
- **Logging**: Structured logging for monitoring and debugging

### **Developer Experience**
- **Type Safety**: Complete type annotations with mypy compatibility
- **Modern Patterns**: Latest async/await patterns throughout
- **Testing**: Comprehensive mocking and async test patterns
- **Documentation**: Clear API docs with examples

## 🐳 Docker Configuration

### **Development (docker-compose.yml)**
```yaml
services:
  web:
    ports: ["8020:8010"]  # Web interface
    volumes: [".:/app"]   # Live reloading
  
  postgres:
    ports: ["9432:5432"]  # Database
    volumes: ["postgres_data:/var/lib/postgresql/data"]
```

### **Production Deployment**
- Health checks on all services
- Volume persistence for database
- Environment-based configuration
- Scalable container architecture

## 🚀 What's New in 2025

### **Technical Modernization**
✅ **SQLAlchemy 2.0**: Latest async patterns with proper session management  
✅ **OpenAI Structured Outputs**: Reliable JSON parsing with Pydantic models  
✅ **FastAPI Lifespan**: Modern startup/shutdown resource management  
✅ **WebSocket Optimization**: Enhanced real-time voice processing  

### **Cricket-Specific Features**
✅ **Specialized AI Prompts**: Cricket coaching and match analysis  
✅ **Comprehensive Data Models**: Batting, bowling, wicket-keeping stats  
✅ **Mental State Tracking**: Psychological aspect monitoring  
✅ **Recovery Monitoring**: Sleep and wellness tracking  

### **Production Features**
✅ **Health Monitoring**: Comprehensive system health endpoints  
✅ **Connection Management**: Advanced WebSocket connection handling  
✅ **Error Recovery**: Robust error handling and retry mechanisms  
✅ **Performance Optimization**: Connection pooling and async processing  

## 🏏 About This Project

This cricket fitness tracker showcases modern Python async patterns and AI integration, specifically designed for young cricket players in Nepal and beyond. It demonstrates production-ready FastAPI applications with real-time voice processing capabilities.

**Perfect for:**
- Young cricket players tracking development
- Coaches monitoring player progress  
- Learning modern async Python patterns
- Building voice-first applications

**Built with ❤️ for the cricket community using cutting-edge 2025 technology** 