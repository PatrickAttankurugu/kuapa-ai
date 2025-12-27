"""
User service for managing user profiles, conversations, and messages
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import uuid

from .models import User, Conversation, Message, Session as DBSession, Analytics
from .logger import logger

class UserService:
    """Service for managing users and their interactions"""
    
    @staticmethod
    def get_or_create_user(db: Session, phone_number: str, name: Optional[str] = None) -> User:
        """Get existing user or create new one"""
        try:
            # Try to get existing user
            user = db.query(User).filter(User.phone_number == phone_number).first()
            
            if user:
                # Update last active time
                user.last_active_at = datetime.utcnow()
                db.commit()
                logger.info(f"Retrieved existing user: {phone_number}")
                return user
            
            # Create new user
            user = User(
                phone_number=phone_number,
                name=name,
                preferred_language='en'
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            logger.info(f"Created new user: {phone_number}")
            
            # Log analytics event
            UserService.log_event(db, user.id, "user_created", {
                "phone_number": phone_number,
                "name": name
            })
            
            return user
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error getting/creating user: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def get_or_create_conversation(db: Session, user_id: uuid.UUID) -> Conversation:
        """Get active conversation or create new one"""
        try:
            # Get most recent active conversation
            conversation = db.query(Conversation).filter(
                Conversation.user_id == user_id,
                Conversation.is_active == True
            ).order_by(desc(Conversation.started_at)).first()
            
            # Create new conversation if none exists or last one is old
            if not conversation:
                conversation = Conversation(user_id=user_id)
                db.add(conversation)
                db.commit()
                db.refresh(conversation)
                logger.info(f"Created new conversation for user {user_id}")
            
            return conversation
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error getting/creating conversation: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def save_message(
        db: Session,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        content: str,
        direction: str,
        message_type: str = 'text',
        language: str = 'en',
        transcribed_text: Optional[str] = None,
        audio_file_path: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Message:
        """Save a message to the database"""
        try:
            message = Message(
                conversation_id=conversation_id,
                user_id=user_id,
                message_type=message_type,
                direction=direction,
                content=content,
                transcribed_text=transcribed_text,
                language=language,
                audio_file_path=audio_file_path,
                extra_data=metadata or {}
            )
            db.add(message)
            
            # Update conversation message count
            conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
            if conversation:
                conversation.message_count += 1
            
            db.commit()
            db.refresh(message)
            
            logger.info(f"Saved {direction} {message_type} message for user {user_id}")
            return message
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving message: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def get_conversation_history(
        db: Session,
        user_id: uuid.UUID,
        limit: int = 10
    ) -> List[Message]:
        """Get recent conversation history for a user"""
        try:
            messages = db.query(Message).filter(
                Message.user_id == user_id
            ).order_by(desc(Message.created_at)).limit(limit).all()
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}", exc_info=True)
            return []
    
    @staticmethod
    def update_user_language(db: Session, user_id: uuid.UUID, language: str):
        """Update user's preferred language"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.preferred_language = language
                db.commit()
                logger.info(f"Updated language for user {user_id}: {language}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating user language: {str(e)}", exc_info=True)
    
    @staticmethod
    def update_user_profile(
        db: Session,
        user_id: uuid.UUID,
        name: Optional[str] = None,
        location: Optional[str] = None,
        farm_size: Optional[str] = None,
        crops: Optional[List[str]] = None
    ):
        """Update user profile information"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                if name:
                    user.name = name
                if location:
                    user.location = location
                if farm_size:
                    user.farm_size = farm_size
                if crops:
                    user.crops = crops
                
                db.commit()
                logger.info(f"Updated profile for user {user_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating user profile: {str(e)}", exc_info=True)
    
    @staticmethod
    def log_event(
        db: Session,
        user_id: Optional[uuid.UUID],
        event_type: str,
        event_data: Optional[Dict] = None
    ):
        """Log an analytics event"""
        try:
            event = Analytics(
                user_id=user_id,
                event_type=event_type,
                event_data=event_data or {}
            )
            db.add(event)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error logging event: {str(e)}")
    
    @staticmethod
    def get_user_stats(db: Session, user_id: uuid.UUID) -> Dict:
        """Get statistics for a user"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {}
            
            total_conversations = db.query(Conversation).filter(
                Conversation.user_id == user_id
            ).count()
            
            total_messages = db.query(Message).filter(
                Message.user_id == user_id,
                Message.direction == 'incoming'
            ).count()
            
            voice_messages = db.query(Message).filter(
                Message.user_id == user_id,
                Message.message_type == 'voice'
            ).count()
            
            return {
                "user_id": str(user_id),
                "phone_number": user.phone_number,
                "member_since": user.created_at.isoformat() if user.created_at else None,
                "last_active": user.last_active_at.isoformat() if user.last_active_at else None,
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "voice_messages": voice_messages,
                "text_messages": total_messages - voice_messages,
                "preferred_language": user.preferred_language
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats: {str(e)}", exc_info=True)
            return {}
