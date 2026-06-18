"""
SQLAlchemy ORM Models — matcht database/schema.sql
"""

import uuid
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.sql import func
from db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class UploadSession(Base):
    __tablename__ = "upload_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    supplier = Column(String(100), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(512))
    status = Column(String(50), default="pending")

    scan1_result = Column(JSONB)
    scan1_started_at = Column(DateTime(timezone=True))
    scan1_completed_at = Column(DateTime(timezone=True))

    scan2_result = Column(JSONB)
    scan2_started_at = Column(DateTime(timezone=True))
    scan2_completed_at = Column(DateTime(timezone=True))

    validation_completed_at = Column(DateTime(timezone=True))
    csv_export_path = Column(String(512))
    csv_export_url = Column(String(512))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ValidationItem(Base):
    __tablename__ = "validation_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("upload_sessions.id", ondelete="CASCADE"), nullable=False)
    item_number = Column(String(20), nullable=False)
    item_name = Column(String(255))
    supplier = Column(String(100))
    missing_fields = Column(ARRAY(String), default=[])
    page_number = Column(Integer)
    column_reference = Column(String(100))
    cell_reference = Column(String(255))
    user_notes = Column(Text)
    validated = Column(Boolean, default=False)
    validated_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("upload_sessions.id", ondelete="SET NULL"), nullable=True)
    resource_type = Column(String(50))
    resource_id = Column(String(255))
    metadata_ = Column("metadata", JSONB)   # "metadata" is een gereserveerd woord in sommige ORMs
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
