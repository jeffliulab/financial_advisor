"""
Database models for the Financial Advisor application.
"""
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, Float, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class User(Base):
    """User model for authentication."""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("Budget", cascade="all, delete-orphan")
    budget_settings = relationship("BudgetSettings", cascade="all, delete-orphan")

class ChatSession(Base):
    """Chat session model for storing chat history."""
    __tablename__ = "chat_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    session_type = Column(String(20), default="chat")  # 'chat' or 'budget'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    """Chat message model for storing individual messages."""
    __tablename__ = "chat_messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")

class File(Base):
    """File model for storing user uploaded files."""
    __tablename__ = "files"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=True)
    filename = Column(String(255), nullable=False)  # Original filename for display
    secure_filename = Column(String(255), nullable=False)  # Secure filename for storage
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(100), nullable=False)
    upload_time = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    session = relationship("ChatSession")

class Budget(Base):
    """Budget model for storing user budget plans."""
    __tablename__ = "budgets"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    year = Column(Integer, nullable=False)  # Budget year
    month = Column(Integer, nullable=True)  # Budget month (null for non-monthly budget)
    is_monthly = Column(Boolean, nullable=False, default=True)  # True for monthly, False for non-monthly
    budget_type = Column(String(20), nullable=False)  # 'annual' or 'monthly' (for display purposes)
    total_income = Column(Float, default=0.0)
    total_expenses = Column(Float, default=0.0)
    savings_goal = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    budget_items = relationship("BudgetItem", back_populates="budget", cascade="all, delete-orphan")

class BudgetItem(Base):
    """Budget item model for storing individual budget categories."""
    __tablename__ = "budget_items"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    budget_id = Column(String(36), ForeignKey("budgets.id"), nullable=False)
    category = Column(String(100), nullable=False)  # e.g., 'Housing', 'Food', 'Transportation'
    item_type = Column(String(20), nullable=False)  # 'income' or 'expense'
    planned_amount = Column(Float, nullable=False, default=0.0)
    actual_amount = Column(Float, default=0.0)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    budget = relationship("Budget", back_populates="budget_items")

class BudgetSettings(Base):
    """Budget settings model for storing user preferences."""
    __tablename__ = "budget_settings"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True)
    show_annual = Column(Boolean, default=True)
    show_monthly = Column(Boolean, default=True)
    currency = Column(String(10), default="USD")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
