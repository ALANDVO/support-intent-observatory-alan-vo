"""SQLAlchemy database entity models for persistence."""

import datetime
import uuid
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


class DatasetRecord(Base):
    __tablename__ = "datasets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(120), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    sample_count = Column(Integer, default=0, nullable=False)
    intent_classes = Column(Text, nullable=False)  # JSON-encoded list of class labels
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    tickets = relationship("TicketRecord", back_populates="dataset", cascade="all, delete-orphan")
    models = relationship("ModelTrainingRecord", back_populates="dataset")


class TicketRecord(Base):
    __tablename__ = "tickets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True)
    external_ref = Column(String(100), nullable=True)
    text = Column(Text, nullable=False)
    actual_intent = Column(String(80), nullable=True)  # Ground truth if labeled
    predicted_intent = Column(String(80), nullable=True)
    confidence = Column(Float, nullable=True)
    margin = Column(Float, nullable=True)
    is_uncertain = Column(Boolean, default=False, nullable=False)
    routing_status = Column(String(50), default="unprocessed", nullable=False)  # auto_routed, human_review, resolved
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    dataset = relationship("DatasetRecord", back_populates="tickets")
    review_item = relationship("ReviewQueueItem", back_populates="ticket", uselist=False, cascade="all, delete-orphan")


class ModelTrainingRecord(Base):
    __tablename__ = "models"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(120), nullable=False)
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(40), default="training", nullable=False)  # ready, training, failed
    hyperparameters = Column(Text, nullable=False)  # JSON-encoded dict
    train_sample_count = Column(Integer, default=0, nullable=False)
    test_sample_count = Column(Integer, default=0, nullable=False)
    accuracy = Column(Float, nullable=True)
    macro_f1 = Column(Float, nullable=True)
    weighted_f1 = Column(Float, nullable=True)
    training_latency_ms = Column(Float, nullable=True)
    model_file_path = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    dataset = relationship("DatasetRecord", back_populates="models")
    evaluation = relationship("EvaluationRecord", back_populates="model", uselist=False, cascade="all, delete-orphan")


class EvaluationRecord(Base):
    __tablename__ = "evaluations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    model_id = Column(String(36), ForeignKey("models.id", ondelete="CASCADE"), nullable=False, unique=True)
    overall_metrics = Column(Text, nullable=False)  # JSON-encoded dict (accuracy, macro/weighted precision/recall/f1)
    per_class_metrics = Column(Text, nullable=False)  # JSON-encoded dict
    confusion_matrix = Column(Text, nullable=False)  # JSON-encoded dict (labels, counts matrix, normalized matrix)
    discriminative_features = Column(Text, nullable=False)  # JSON-encoded dict (top keywords per intent)
    baseline_comparison = Column(Text, nullable=False)  # JSON-encoded dict (ML model vs keyword baseline)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    model = relationship("ModelTrainingRecord", back_populates="evaluation")


class ReviewQueueItem(Base):
    __tablename__ = "review_queue"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    ticket_id = Column(String(36), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, unique=True)
    predicted_intent = Column(String(80), nullable=False)
    confidence = Column(Float, nullable=False)
    margin = Column(Float, nullable=False)
    uncertainty_reason = Column(String(200), nullable=False)
    status = Column(String(40), default="pending", nullable=False)  # pending, resolved, dismissed
    resolved_intent = Column(String(80), nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    resolved_by = Column(String(120), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    ticket = relationship("TicketRecord", back_populates="review_item")


class AuditLogRecord(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    actor_username = Column(String(120), nullable=False)
    actor_role = Column(String(50), nullable=False)
    action = Column(String(80), nullable=False)
    resource_type = Column(String(80), nullable=False)
    resource_id = Column(String(120), nullable=True)
    details = Column(Text, nullable=True)  # JSON-encoded details
    status = Column(String(40), default="success", nullable=False)
