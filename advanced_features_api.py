"""
Advanced Features API for Whisper AI Assistant.

This module provides endpoints for:
- Conversation history and context management
- User preferences and personalization
- Integration ecosystem
- Analytics and insights
- Scheduled tasks and proactive intelligence
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models import (
    get_db,
    User,
    Conversation,
    Message,
    ContextItem,
    UserPreference,
    IntegrationConfig,
    UserAnalytics,
    ScheduledTask,
    LanguageCode,
    IntegrationProvider,
)

# ============================================================================
# PYDANTIC MODELS (Request/Response)
# ============================================================================

class MessageCreate(BaseModel):
    role: str  # "user", "assistant", "system"
    content: str
    language: Optional[str] = None

class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    timestamp: datetime
    language: Optional[str] = None
    confidence_score: Optional[float] = None
    tokens_used: Optional[int] = None

class ConversationCreate(BaseModel):
    title: Optional[str] = None

class ConversationResponse(BaseModel):
    id: int
    conversation_id: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    archived: bool
    messages: List[MessageResponse] = []

class UserPreferenceUpdate(BaseModel):
    preferred_language: Optional[str] = None
    voice_speed: Optional[float] = None
    response_length: Optional[str] = None
    privacy_mode: Optional[bool] = None

class IntegrationConfigResponse(BaseModel):
    id: int
    provider: str
    is_enabled: bool
    created_at: datetime
    synced_at: Optional[datetime] = None

class ContextItemCreate(BaseModel):
    item_type: str
    key: str
    value: str
    expires_at: Optional[datetime] = None

class ScheduledTaskCreate(BaseModel):
    task_type: str
    title: str
    description: Optional[str] = None
    scheduled_time: datetime
    recurrence: Optional[str] = None

class ScheduledTaskResponse(BaseModel):
    id: int
    task_type: str
    title: str
    description: Optional[str] = None
    scheduled_time: datetime
    is_completed: bool
    recurrence: Optional[str] = None


# ============================================================================
# ROUTER SETUP
# ============================================================================

router = APIRouter(prefix="/api/advanced", tags=["advanced-features"])


# ============================================================================
# USER MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/users/{user_id}/preferences")
async def update_user_preferences(
    user_id: str,
    preferences: UserPreferenceUpdate,
    db: Session = Depends(get_db)
):
    """Update user preferences for voice, language, and behavior."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        user = User(user_id=user_id)
        db.add(user)
        db.flush()

    # Update preferences
    if preferences.preferred_language:
        user.preferred_language = preferences.preferred_language
    if preferences.voice_speed is not None:
        user.voice_speed = max(0.5, min(2.0, preferences.voice_speed))
    if preferences.response_length:
        user.response_length = preferences.response_length
    if preferences.privacy_mode is not None:
        user.privacy_mode = preferences.privacy_mode

    db.commit()
    return {
        "status": "success",
        "message": "Preferences updated",
        "user_id": user.user_id,
        "preferences": {
            "language": user.preferred_language,
            "voice_speed": user.voice_speed,
            "response_length": user.response_length,
            "privacy_mode": user.privacy_mode,
        }
    }


@router.get("/users/{user_id}/preferences")
async def get_user_preferences(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get current user preferences."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        return {"error": "User not found"}

    return {
        "user_id": user.user_id,
        "preferred_language": user.preferred_language,
        "voice_speed": user.voice_speed,
        "response_length": user.response_length,
        "privacy_mode": user.privacy_mode,
        "created_at": user.created_at,
    }


# ============================================================================
# CONVERSATION HISTORY ENDPOINTS
# ============================================================================

@router.post("/conversations")
async def create_conversation(
    user_id: str,
    conv_create: ConversationCreate,
    db: Session = Depends(get_db)
):
    """Create a new conversation."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        user = User(user_id=user_id)
        db.add(user)
        db.flush()

    import uuid
    conversation = Conversation(
        user_id=user.id,
        conversation_id=str(uuid.uuid4()),
        title=conv_create.title or f"Conversation {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
    )
    db.add(conversation)
    db.commit()

    return {
        "id": conversation.id,
        "conversation_id": conversation.conversation_id,
        "title": conversation.title,
        "created_at": conversation.created_at,
    }


@router.get("/conversations")
async def list_conversations(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    archived: bool = Query(False),
    db: Session = Depends(get_db)
):
    """List all conversations for a user."""
    query = db.query(Conversation).filter(
        Conversation.user_id == db.query(User.id).filter(User.user_id == user_id).scalar(),
        Conversation.archived == archived
    )
    
    conversations = query.order_by(desc(Conversation.updated_at)).offset(skip).limit(limit).all()
    total = query.count()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "conversations": [
            {
                "id": c.id,
                "conversation_id": c.conversation_id,
                "title": c.title,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
                "message_count": len(c.messages),
            }
            for c in conversations
        ]
    }


@router.post("/conversations/{conversation_id}/messages")
async def add_message(
    user_id: str,
    conversation_id: str,
    message: MessageCreate,
    db: Session = Depends(get_db)
):
    """Add a message to a conversation."""
    conversation = db.query(Conversation).filter(
        Conversation.conversation_id == conversation_id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msg = Message(
        conversation_id=conversation.id,
        role=message.role,
        content=message.content,
        language=message.language,
    )
    db.add(msg)
    db.commit()

    return {
        "id": msg.id,
        "role": msg.role,
        "content": msg.content,
        "timestamp": msg.timestamp,
        "language": msg.language,
    }


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    user_id: str,
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """Get all messages in a conversation."""
    conversation = db.query(Conversation).filter(
        Conversation.conversation_id == conversation_id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = db.query(Message).filter(
        Message.conversation_id == conversation.id
    ).order_by(Message.timestamp).all()

    return {
        "conversation_id": conversation_id,
        "message_count": len(messages),
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp,
                "language": m.language,
            }
            for m in messages
        ]
    }


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    user_id: str,
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific conversation with its messages."""
    conversation = db.query(Conversation).filter(
        Conversation.conversation_id == conversation_id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = db.query(Message).filter(
        Message.conversation_id == conversation.id
    ).order_by(Message.timestamp).all()

    return {
        "id": conversation.id,
        "conversation_id": conversation.conversation_id,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "archived": conversation.archived,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp,
                "language": m.language,
                "tokens_used": m.tokens_used,
            }
            for m in messages
        ]
    }


# ============================================================================
# CONTEXT MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/conversations/{conversation_id}/context")
async def add_context(
    user_id: str,
    conversation_id: str,
    context: ContextItemCreate,
    db: Session = Depends(get_db)
):
    """Add context information to a conversation."""
    conversation = db.query(Conversation).filter(
        Conversation.conversation_id == conversation_id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    ctx = ContextItem(
        conversation_id=conversation.id,
        item_type=context.item_type,
        key=context.key,
        value=context.value,
        expires_at=context.expires_at,
    )
    db.add(ctx)
    db.commit()

    return {
        "id": ctx.id,
        "item_type": ctx.item_type,
        "key": ctx.key,
        "value": ctx.value,
    }


@router.get("/conversations/{conversation_id}/context")
async def get_context(
    user_id: str,
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """Get all context items for a conversation."""
    conversation = db.query(Conversation).filter(
        Conversation.conversation_id == conversation_id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    context_items = db.query(ContextItem).filter(
        ContextItem.conversation_id == conversation.id
    ).all()

    return {
        "conversation_id": conversation_id,
        "context": [
            {
                "item_type": ci.item_type,
                "key": ci.key,
                "value": ci.value,
                "expires_at": ci.expires_at,
            }
            for ci in context_items
        ]
    }


# ============================================================================
# INTEGRATION ENDPOINTS
# ============================================================================

@router.post("/integrations/{provider}")
async def setup_integration(
    user_id: str,
    provider: str,
    access_token: str,
    refresh_token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Set up or update an integration."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        user = User(user_id=user_id)
        db.add(user)
        db.flush()

    integration = db.query(IntegrationConfig).filter(
        IntegrationConfig.user_id == user.id,
        IntegrationConfig.provider == provider
    ).first()

    if not integration:
        integration = IntegrationConfig(
            user_id=user.id,
            provider=provider,
            access_token=access_token,
            refresh_token=refresh_token,
        )
        db.add(integration)
    else:
        integration.access_token = access_token
        if refresh_token:
            integration.refresh_token = refresh_token
        integration.expires_at = None

    db.commit()

    return {
        "status": "success",
        "provider": provider,
        "is_enabled": integration.is_enabled,
        "created_at": integration.created_at,
    }


@router.get("/integrations")
async def list_integrations(
    user_id: str,
    db: Session = Depends(get_db)
):
    """List all integrations for a user."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        return {"integrations": []}

    integrations = db.query(IntegrationConfig).filter(
        IntegrationConfig.user_id == user.id
    ).all()

    return {
        "total": len(integrations),
        "integrations": [
            {
                "provider": i.provider,
                "is_enabled": i.is_enabled,
                "created_at": i.created_at,
                "synced_at": i.synced_at,
            }
            for i in integrations
        ]
    }


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/analytics/{user_id}")
async def get_user_analytics(
    user_id: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get analytics for a user over the last N days."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        return {"error": "User not found"}

    from datetime import timedelta
    start_date = datetime.utcnow() - timedelta(days=days)

    analytics = db.query(UserAnalytics).filter(
        UserAnalytics.user_id == user.id,
        UserAnalytics.date >= start_date
    ).all()

    total_messages = sum(a.messages_sent + a.messages_received for a in analytics)
    total_tokens = sum(a.tokens_used for a in analytics)
    total_cost = sum(a.api_cost for a in analytics)

    return {
        "user_id": user_id,
        "days": days,
        "metrics": {
            "total_messages": total_messages,
            "total_tokens": total_tokens,
            "total_cost": f"${total_cost:.2f}",
            "average_cost_per_day": f"${total_cost / max(1, len(analytics)):.2f}",
        },
        "daily_breakdown": [
            {
                "date": a.date.isoformat(),
                "messages_sent": a.messages_sent,
                "messages_received": a.messages_received,
                "tokens_used": a.tokens_used,
                "cost": f"${a.api_cost:.2f}",
            }
            for a in sorted(analytics, key=lambda a: a.date)
        ]
    }


# ============================================================================
# SCHEDULED TASKS (PROACTIVE INTELLIGENCE)
# ============================================================================

@router.post("/tasks")
async def create_scheduled_task(
    user_id: str,
    task: ScheduledTaskCreate,
    db: Session = Depends(get_db)
):
    """Create a scheduled task or reminder."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        user = User(user_id=user_id)
        db.add(user)
        db.flush()

    scheduled_task = ScheduledTask(
        user_id=user.id,
        task_type=task.task_type,
        title=task.title,
        description=task.description,
        scheduled_time=task.scheduled_time,
        recurrence=task.recurrence,
    )
    db.add(scheduled_task)
    db.commit()

    return {
        "id": scheduled_task.id,
        "task_type": scheduled_task.task_type,
        "title": scheduled_task.title,
        "scheduled_time": scheduled_task.scheduled_time,
    }


@router.get("/tasks")
async def list_scheduled_tasks(
    user_id: str,
    completed: bool = Query(False),
    db: Session = Depends(get_db)
):
    """List scheduled tasks for a user."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        return {"tasks": []}

    tasks = db.query(ScheduledTask).filter(
        ScheduledTask.user_id == user.id,
        ScheduledTask.is_completed == completed
    ).order_by(ScheduledTask.scheduled_time).all()

    return {
        "total": len(tasks),
        "tasks": [
            {
                "id": t.id,
                "task_type": t.task_type,
                "title": t.title,
                "description": t.description,
                "scheduled_time": t.scheduled_time,
                "recurrence": t.recurrence,
            }
            for t in tasks
        ]
    }


@router.put("/tasks/{task_id}/complete")
async def complete_task(
    user_id: str,
    task_id: int,
    db: Session = Depends(get_db)
):
    """Mark a task as completed."""
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.is_completed = True
    task.completed_at = datetime.utcnow()
    db.commit()

    return {"status": "success", "task_id": task_id, "completed_at": task.completed_at}
