"""
SQLAlchemy models for database persistence.
"""
from datetime import datetime

try:
    from sqlalchemy import (
        JSON,
        Boolean,
        Column,
        DateTime,
        ForeignKey,
        Integer,
        String,
        Text,
    )
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import relationship

    Base = declarative_base()

    class UserModel(Base):
        """User database model."""
        __tablename__ = "users"

        id = Column(String, primary_key=True)
        email = Column(String, nullable=True, unique=True)
        phone_number = Column(String, nullable=True)
        telegram_id = Column(String, nullable=True)
        is_active = Column(Boolean, default=True, nullable=False)
        preferences = Column(JSON, default=dict)
        created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

        # Relationships
        notifications = relationship("NotificationModel", back_populates="recipient")


    class NotificationModel(Base):
        """Notification database model."""
        __tablename__ = "notifications"

        id = Column(String, primary_key=True)
        recipient_id = Column(String, ForeignKey("users.id"), nullable=False)
        message_template = Column(Text, nullable=False)
        message_variables = Column(JSON, default=dict)
        channels = Column(JSON, nullable=False)  # List of channel names
        priority = Column(String, nullable=False)
        scheduled_at = Column(DateTime, nullable=False)
        sent_at = Column(DateTime, nullable=True)
        retry_policy = Column(JSON, default=dict)
        metadata = Column(JSON, default=dict)
        created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

        # Relationships
        recipient = relationship("UserModel", back_populates="notifications")
        deliveries = relationship("DeliveryModel", back_populates="notification")


    class DeliveryModel(Base):
        """Delivery database model."""
        __tablename__ = "deliveries"

        id = Column(String, primary_key=True)
        notification_id = Column(String, ForeignKey("notifications.id"), nullable=False)
        channel = Column(String, nullable=False)
        provider = Column(String, nullable=False)
        status = Column(String, nullable=False)
        created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
        completed_at = Column(DateTime, nullable=True)

        # Relationships
        notification = relationship("NotificationModel", back_populates="deliveries")
        attempts = relationship("DeliveryAttemptModel", back_populates="delivery")


    class DeliveryAttemptModel(Base):
        """Delivery attempt database model."""
        __tablename__ = "delivery_attempts"

        id = Column(Integer, primary_key=True, autoincrement=True)
        delivery_id = Column(String, ForeignKey("deliveries.id"), nullable=False)
        attempt_number = Column(Integer, nullable=False)
        provider = Column(String, nullable=False)
        attempted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
        success = Column(Boolean, nullable=False)
        error_message = Column(Text, nullable=True)
        response_data = Column(JSON, default=dict)

        # Relationships
        delivery = relationship("DeliveryModel", back_populates="attempts")

except ImportError:
    # Fallback for when SQLAlchemy is not available
    Base = None
    UserModel = None
    NotificationModel = None
    DeliveryModel = None
    DeliveryAttemptModel = None
