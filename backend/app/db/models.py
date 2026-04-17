"""
SQLAlchemy ORM Models — HCP Interaction Logger

Maps exactly to the PostgreSQL schema defined in schema.sql.
All tables use UUID primary keys and maintain foreign key relationships.
"""

import uuid
from datetime import date, time, datetime

from sqlalchemy import (
    Column, String, Text, Integer, Boolean, Date, Time,
    DateTime, ForeignKey, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.sql import func


# ── Base ────────────────────────────────────────────────────

class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


# ── 1. HCPs ────────────────────────────────────────────────

class HCP(Base):
    """Healthcare Professional profile."""

    __tablename__ = "hcps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    specialty = Column(String(150), nullable=False)
    location = Column(String(255))
    hospital = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    interactions = relationship("Interaction", back_populates="hcp", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_hcps_name", "name"),
        Index("idx_hcps_specialty", "specialty"),
        Index("idx_hcps_location", "location"),
    )

    def __repr__(self):
        return f"<HCP(id={self.id}, name='{self.name}', specialty='{self.specialty}')>"


# ── 2. Interactions ─────────────────────────────────────────

class Interaction(Base):
    """Logged meeting / call / interaction with an HCP."""

    __tablename__ = "interactions"

    INTERACTION_TYPES = ("in-person", "virtual", "phone", "email", "conference")
    SENTIMENT_VALUES = ("positive", "neutral", "negative")

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hcp_id = Column(UUID(as_uuid=True), ForeignKey("hcps.id", ondelete="CASCADE"), nullable=False)
    interaction_type = Column(String(50), nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time)
    attendees = Column(Text)
    topics_discussed = Column(Text)
    outcomes = Column(Text)
    follow_up_actions = Column(Text)
    sentiment = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    hcp = relationship("HCP", back_populates="interactions")
    materials = relationship("MaterialShared", back_populates="interaction", cascade="all, delete-orphan")
    samples = relationship("SampleDistributed", back_populates="interaction", cascade="all, delete-orphan")
    follow_up_suggestions = relationship("FollowUpSuggestion", back_populates="interaction", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "interaction_type IN ('in-person', 'virtual', 'phone', 'email', 'conference')",
            name="chk_interaction_type",
        ),
        CheckConstraint(
            "sentiment IN ('positive', 'neutral', 'negative')",
            name="chk_sentiment",
        ),
        Index("idx_interactions_hcp_id", "hcp_id"),
        Index("idx_interactions_date", "date"),
        Index("idx_interactions_type", "interaction_type"),
        Index("idx_interactions_sentiment", "sentiment"),
    )

    def __repr__(self):
        return f"<Interaction(id={self.id}, hcp_id={self.hcp_id}, type='{self.interaction_type}', date={self.date})>"


# ── 3. Materials Shared ────────────────────────────────────

class MaterialShared(Base):
    """Collateral / materials shared during an interaction."""

    __tablename__ = "materials_shared"

    MATERIAL_TYPES = ("brochure", "clinical_study", "presentation", "product_info", "sample_card", "other")

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interaction_id = Column(UUID(as_uuid=True), ForeignKey("interactions.id", ondelete="CASCADE"), nullable=False)
    material_name = Column(String(255), nullable=False)
    material_type = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    interaction = relationship("Interaction", back_populates="materials")

    __table_args__ = (
        CheckConstraint(
            "material_type IN ('brochure', 'clinical_study', 'presentation', 'product_info', 'sample_card', 'other')",
            name="chk_material_type",
        ),
        Index("idx_materials_interaction_id", "interaction_id"),
    )

    def __repr__(self):
        return f"<MaterialShared(id={self.id}, name='{self.material_name}')>"


# ── 4. Samples Distributed ─────────────────────────────────

class SampleDistributed(Base):
    """Drug samples distributed to an HCP during an interaction."""

    __tablename__ = "samples_distributed"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interaction_id = Column(UUID(as_uuid=True), ForeignKey("interactions.id", ondelete="CASCADE"), nullable=False)
    sample_name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    interaction = relationship("Interaction", back_populates="samples")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_quantity_positive"),
        Index("idx_samples_interaction_id", "interaction_id"),
    )

    def __repr__(self):
        return f"<SampleDistributed(id={self.id}, name='{self.sample_name}', qty={self.quantity})>"


# ── 5. Follow-Up Suggestions ───────────────────────────────

class FollowUpSuggestion(Base):
    """Follow-up suggestions — AI-generated or manually entered."""

    __tablename__ = "follow_up_suggestions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interaction_id = Column(UUID(as_uuid=True), ForeignKey("interactions.id", ondelete="CASCADE"), nullable=False)
    suggestion_text = Column(Text, nullable=False)
    generated_by_ai = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    interaction = relationship("Interaction", back_populates="follow_up_suggestions")

    __table_args__ = (
        Index("idx_follow_ups_interaction_id", "interaction_id"),
        Index("idx_follow_ups_ai", "generated_by_ai"),
    )

    def __repr__(self):
        return f"<FollowUpSuggestion(id={self.id}, ai={self.generated_by_ai})>"
