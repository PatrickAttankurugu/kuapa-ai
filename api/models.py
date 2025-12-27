"""
SQLAlchemy models for Kuapa AI database
Maps to PostgreSQL tables with pgVector support
"""

from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text, ARRAY, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
# from pgvector.sqlalchemy import Vector  # Uncomment when pgVector is installed
import uuid
from datetime import datetime

from .database import Base

class User(Base):
    """User model - stores farmer profiles"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255))
    preferred_language = Column(String(5), default='en')
    location = Column(String(255))
    farm_size = Column(String(50))
    crops = Column(ARRAY(Text))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_active_at = Column(DateTime(timezone=True), server_default=func.now())
    extra_data = Column('metadata', JSONB, default={})
    is_active = Column(Boolean, default=True)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(phone={self.phone_number}, name={self.name})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "phone_number": self.phone_number,
            "name": self.name,
            "preferred_language": self.preferred_language,
            "location": self.location,
            "farm_size": self.farm_size,
            "crops": self.crops,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_active_at": self.last_active_at.isoformat() if self.last_active_at else None,
            "is_active": self.is_active
        }

class Conversation(Base):
    """Conversation model - groups messages into sessions"""
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True))
    message_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    extra_data = Column('metadata', JSONB, default={})
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, user_id={self.user_id}, messages={self.message_count})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "message_count": self.message_count,
            "is_active": self.is_active
        }

class Message(Base):
    """Message model - stores individual chat messages with embeddings"""
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message_type = Column(String(20), nullable=False)  # 'text', 'voice', 'system'
    direction = Column(String(10), nullable=False)  # 'incoming', 'outgoing'
    content = Column(Text, nullable=False)
    transcribed_text = Column(Text)
    language = Column(String(5))
    audio_file_path = Column(Text)
    #embedding = Column(Vector(768))  # pgVector for semantic search
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    extra_data = Column('metadata', JSONB, default={})
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    user = relationship("User", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, type={self.message_type}, direction={self.direction})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "user_id": str(self.user_id),
            "message_type": self.message_type,
            "direction": self.direction,
            "content": self.content,
            "transcribed_text": self.transcribed_text,
            "language": self.language,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Session(Base):
    """Session model - tracks active WhatsApp sessions"""
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"))
    session_token = Column(String(255), unique=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    extra_data = Column('metadata', JSONB, default={})
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    conversation = relationship("Conversation", back_populates="sessions")
    
    def __repr__(self):
        return f"<Session(id={self.id}, user_id={self.user_id}, active={self.is_active})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "conversation_id": str(self.conversation_id) if self.conversation_id else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "last_activity_at": self.last_activity_at.isoformat() if self.last_activity_at else None,
            "is_active": self.is_active
        }

class UserPreference(Base):
    """User preferences model"""
    __tablename__ = "user_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    receive_notifications = Column(Boolean, default=True)
    notification_time = Column(DateTime)
    topics_of_interest = Column(ARRAY(Text))
    preferences = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="preferences")
    
    def __repr__(self):
        return f"<UserPreference(user_id={self.user_id})>"

class Analytics(Base):
    """Analytics model - tracks user interactions and events"""
    __tablename__ = "analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    event_type = Column(String(50), nullable=False)
    event_data = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Analytics(event={self.event_type}, user_id={self.user_id})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id) if self.user_id else None,
            "event_type": self.event_type,
            "event_data": self.event_data,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
