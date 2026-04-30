"""
Database models for Whisper AI Assistant Advanced Features.

This module defines SQLAlchemy models for:
- Conversation history and context management
- User preferences and personalization
- Integration configurations
- Analytics and usage tracking
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
import os

# Database URL configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./whisper_assistant.db"  # Default to SQLite for local development
)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

Base = declarative_base()


# ============================================================================
# ENUMS
# ============================================================================

class LanguageCode(str, Enum):
    """Supported languages for the assistant."""
    EN = "en"
    ES = "es"
    FR = "fr"
    DE = "de"
    IT = "it"
    PT = "pt"
    JA = "ja"
    ZH = "zh"
    KO = "ko"
    RU = "ru"
    AR = "ar"
    HI = "hi"
    NL = "nl"
    PL = "pl"
    TR = "tr"


class IntegrationProvider(str, Enum):
    """Supported external service integrations."""
    GOOGLE_CALENDAR = "google_calendar"
    GMAIL = "gmail"
    SLACK = "slack"
    NOTION = "notion"
    TODOIST = "todoist"
    SPOTIFY = "spotify"
    PHILIPS_HUE = "philips_hue"
    SMARTTHINGS = "smartthings"
    OPENWEATHER = "openweather"
    NEWS_API = "news_api"


# ============================================================================
# CORE MODELS
# ============================================================================

class User(Base):
    """User account and preferences."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), unique=True, index=True)  # External user identifier
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Preferences
    preferred_language = Column(String(10), default=LanguageCode.EN.value)
    voice_speed = Column(Float, default=1.0)  # 0.5 to 2.0
    response_length = Column(String(20), default="medium")  # short, medium, long
    privacy_mode = Column(Boolean, default=False)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", cascade="all, delete-orphan")
    integrations = relationship("IntegrationConfig", back_populates="user", cascade="all, delete-orphan")
    analytics = relationship("UserAnalytics", back_populates="user", cascade="all, delete-orphan")


class Conversation(Base):
    """Conversation history with context management."""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    conversation_id = Column(String(255), unique=True, index=True)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    archived = Column(Boolean, default=False)
    
    # Context tracking
    context_summary = Column(Text, nullable=True)  # Compressed context for efficiency
    has_attachments = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    context_items = relationship("ContextItem", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Individual messages within conversations."""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), index=True)
    role = Column(String(20))  # "user", "assistant", "system"
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Metadata
    language = Column(String(10), nullable=True)
    confidence_score = Column(Float, nullable=True)  # STT confidence
    tokens_used = Column(Integer, nullable=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    attachments = relationship("Attachment", back_populates="message", cascade="all, delete-orphan")


class ContextItem(Base):
    """Context information for intelligent responses."""
    __tablename__ = "context_items"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), index=True)
    item_type = Column(String(50))  # "user_preference", "previous_context", "external_data"
    key = Column(String(255))
    value = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Optional expiration
    
    # Relationships
    conversation = relationship("Conversation", back_populates="context_items")


class Attachment(Base):
    """File attachments in messages (images, PDFs, etc)."""
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), index=True)
    file_name = Column(String(255))
    file_type = Column(String(50))  # "image", "pdf", "document"
    file_path = Column(String(500))  # S3/Blob storage path
    file_size = Column(Integer)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    message = relationship("Message", back_populates="attachments")


class UserPreference(Base):
    """Detailed user preferences and settings."""
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    preference_key = Column(String(255))
    preference_value = Column(Text)
    category = Column(String(100))  # "voice", "behavior", "notifications", "accessibility"
    
    # Relationships
    user = relationship("User", back_populates="preferences")


class IntegrationConfig(Base):
    """External service integrations configuration."""
    __tablename__ = "integration_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    provider = Column(String(50))  # GoogleCalendar, Gmail, Slack, etc.
    is_enabled = Column(Boolean, default=True)
    access_token = Column(Text)  # Encrypted in production
    refresh_token = Column(Text, nullable=True)  # Encrypted in production
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    synced_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="integrations")


class ScheduledTask(Base):
    """Proactive intelligence - scheduled actions and reminders."""
    __tablename__ = "scheduled_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    task_type = Column(String(100))  # "reminder", "scheduled_briefing", "routine"
    title = Column(String(255))
    description = Column(Text, nullable=True)
    scheduled_time = Column(DateTime, index=True)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Recurrence pattern
    recurrence = Column(String(50), nullable=True)  # "daily", "weekly", "monthly"


class UserAnalytics(Base):
    """Usage analytics and insights."""
    __tablename__ = "user_analytics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    date = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Usage metrics
    messages_sent = Column(Integer, default=0)
    messages_received = Column(Integer, default=0)
    total_conversation_time = Column(Integer, default=0)  # seconds
    integrations_used = Column(Integer, default=0)
    files_processed = Column(Integer, default=0)
    
    # Cost tracking
    tokens_used = Column(Integer, default=0)
    api_cost = Column(Float, default=0.0)
    
    # Relationships
    user = relationship("User", back_populates="analytics")


class UserDetectionMemory(Base):
    """Store user's custom object labels learned from video calls"""
    __tablename__ = "user_detection_memory"
    
    id = Column(String, primary_key=True, default=lambda: str(__import__('uuid').uuid4()))
    user_id = Column(String, nullable=False, index=True)
    object_label = Column(String, nullable=False)  # e.g., "laptop"
    user_name = Column(String, nullable=False)  # e.g., "My MacBook Pro"
    custom_info = Column(String, nullable=True)  # e.g., "silver 16-inch"
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DetectionHistory(Base):
    """Store history of detected objects during video calls"""
    __tablename__ = "detection_history"
    
    id = Column(String, primary_key=True, default=lambda: str(__import__('uuid').uuid4()))
    user_id = Column(String, nullable=False, index=True)
    session_id = Column(String, nullable=False)  # Video call session ID
    
    detected_objects = Column(String, nullable=False)  # JSON as string
    summary = Column(String, nullable=True)  # Natural language summary
    total_detections = Column(Integer, default=0)
    processing_time = Column(Float, nullable=True)  # Processing duration in seconds
    
    camera_used = Column(String, default="front")  # "front" or "back"
    
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_db():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)
    print("[v0] Database tables created successfully")


def get_db():
    """Dependency for getting database session."""
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()
