"""
API Routes - User Message Interface

Endpoint: POST /api/user-message

Request Body:
{
    "session_id": str,
    "message": str,
    "context": {
        "content": str,
        "mode": "code" | "story"
    },
    "provider": {
        "type": "openai" | "gemini",
        "api_key": str,
        "base_url": Optional[str],
        "model_name": Optional[str]
    }
}

Response:
{
    "session_id": str,
    "message_id": str,
    "status": "processing" | "completed" | "error",
    "timestamp": float
}

The actual AI response will be sent via WebSocket connection
"""

# TODO: Implementation
