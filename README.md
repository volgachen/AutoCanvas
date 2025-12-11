# AI Canvas Backend

Python FastAPI backend server for AI Canvas application. Handles AI provider communications and maintains WebSocket connections with the frontend.

## Architecture Overview

### Design Pattern: Separation of Concerns

The backend follows a clean architecture pattern with clear separation between:
- **Routes**: API endpoint definitions
- **Services**: Business logic and external API integrations
- **Models**: Data validation and serialization

### Communication Flow

```
Frontend (React)
    ↓
    ├─→ HTTP POST /api/user-message (send user message)
    │   └─→ Returns: { session_id, message_id, status }
    │
    └─→ WebSocket /ws (receive AI responses)
        ├─→ Send: heartbeat messages
        └─→ Receive: AI response streams
```

## Project Structure

```
backend/
├── main.py                          # Application entry point
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
├── .gitignore                       # Git ignore rules
│
├── app/
│   ├── __init__.py
│   ├── config.py                    # Configuration management
│   ├── utils.py                     # Utility functions
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── user_message.py          # POST /api/user-message endpoint
│   │   └── heartbeat.py             # WebSocket /ws endpoint
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── websocket_manager.py     # WebSocket connection management
│   │   ├── session_manager.py       # Session tracking
│   │   │
│   │   └── ai/
│   │       ├── __init__.py
│   │       ├── base.py              # Base AI service interface
│   │       ├── factory.py           # AI service factory
│   │       ├── openai_service.py    # OpenAI API integration
│   │       └── gemini_service.py    # Gemini API integration
│   │
│   └── models/
│       ├── __init__.py
│       └── schemas.py               # Pydantic models
```

## API Interfaces

### 1. User Message Interface

**Endpoint:** `POST /api/user-message`

**Purpose:** Accept user messages and initiate AI processing

**Request:**
```json
{
  "session_id": "uuid-string",
  "message": "User's message text",
  "context": {
    "content": "Current editor content",
    "mode": "code" | "story"
  },
  "provider": {
    "type": "openai" | "gemini",
    "api_key": "user-api-key",
    "base_url": "optional-custom-endpoint",
    "model_name": "optional-model-name"
  }
}
```

**Response:**
```json
{
  "session_id": "uuid-string",
  "message_id": "uuid-string",
  "status": "processing",
  "timestamp": 1234567890.123
}
```

**Flow:**
1. Validate request data
2. Create/retrieve session
3. Queue AI processing task
4. Return immediately with message ID
5. AI response streamed via WebSocket

### 2. Heartbeat Interface

**Endpoint:** `WebSocket /ws`

**Purpose:** Maintain persistent connection for real-time updates and heartbeats

**Client → Server Messages:**

```json
// Initial connection
{
  "type": "connect",
  "session_id": "optional-uuid"
}

// Heartbeat ping
{
  "type": "heartbeat",
  "session_id": "uuid-string",
  "timestamp": 1234567890.123
}
```

**Server → Client Messages:**

```json
// Connection acknowledgment
{
  "type": "connected",
  "session_id": "uuid-string",
  "timestamp": 1234567890.123
}

// Heartbeat response
{
  "type": "heartbeat-ack",
  "session_id": "uuid-string",
  "timestamp": 1234567890.123
}

// AI response stream (sent multiple times)
{
  "type": "ai-response",
  "session_id": "uuid-string",
  "message_id": "uuid-string",
  "content": "AI response text chunk",
  "is_complete": false,
  "timestamp": 1234567890.123
}

// Error message
{
  "type": "error",
  "session_id": "uuid-string",
  "error": "Error description",
  "timestamp": 1234567890.123
}
```

## Key Components

### WebSocket Manager (`app/services/websocket_manager.py`)
- Maintains active WebSocket connections
- Routes messages to appropriate sessions
- Handles heartbeat monitoring
- Broadcasts AI responses to clients

### Session Manager (`app/services/session_manager.py`)
- Tracks active user sessions
- Stores session metadata
- Implements session timeout logic
- Cleans up expired sessions

### AI Services (`app/services/ai/`)

**Base Service (`base.py`)**
- Abstract base class defining AI service interface
- Methods: `send_message()`, `stream_response()`

**OpenAI Service (`openai_service.py`)**
- Integrates with OpenAI and OpenAI-compatible APIs
- Supports custom base URLs
- Handles streaming responses

**Gemini Service (`gemini_service.py`)**
- Integrates with Google Gemini API
- Handles Gemini-specific request/response format

**Factory (`factory.py`)**
- Creates appropriate AI service instance based on provider type
- Validates provider configuration

## Setup Instructions

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 4. Run Development Server

```bash
# Using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or using Python
python -m uvicorn main:app --reload
```

The server will start at `http://localhost:8000`

### 5. API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Configuration

Environment variables (`.env`):

```bash
# Server
HOST=0.0.0.0
PORT=8000
RELOAD=True

# CORS
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5174

# WebSocket
WS_HEARTBEAT_INTERVAL=30
WS_HEARTBEAT_TIMEOUT=60

# Sessions
SESSION_TIMEOUT=3600

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## Security Considerations

- API keys are **never stored** on the backend
- Each request includes provider credentials
- WebSocket connections validated per session
- CORS properly configured
- No persistent storage of user data

## Development Guidelines

### Adding a New AI Provider

1. Create new service in `app/services/ai/{provider}_service.py`
2. Inherit from `BaseAIService`
3. Implement required methods
4. Register in `factory.py`

### Testing WebSocket Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'connect',
    session_id: 'test-session'
  }));
};

ws.onmessage = (event) => {
  console.log('Received:', JSON.parse(event.data));
};
```

## Deployment

### Using Docker (TODO)

```bash
docker build -t ai-canvas-backend .
docker run -p 8000:8000 ai-canvas-backend
```

### Using Production Server

```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

## Tech Stack

- **FastAPI**: Modern async web framework
- **Uvicorn**: ASGI server
- **WebSockets**: Real-time communication
- **Pydantic**: Data validation
- **httpx/aiohttp**: Async HTTP clients for AI APIs

## Future Enhancements

- [ ] Rate limiting per session
- [ ] Message queue for high load
- [ ] Redis for session storage
- [ ] Metrics and monitoring
- [ ] Docker containerization
- [ ] Unit and integration tests
- [ ] CI/CD pipeline

---

**Note:** This is a framework structure with TODO markers. Implementation details should be added based on specific requirements.
