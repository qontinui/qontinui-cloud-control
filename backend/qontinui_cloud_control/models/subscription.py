from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class SubscriptionStatus(StrEnum):
    """Stripe subscription status"""

    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    TRIALING = "trialing"
    UNPAID = "unpaid"


class SubscriptionTier(StrEnum):
    """Subscription tiers"""

    FREE = "free"
    HOBBY = "hobby"
    PRO = "pro"


class Subscription(Base):
    """User subscription information.

    Lives in the ``cloud`` schema (see
    ``qontinui-web/backend/alembic/versions/cloud_schema_initial_tables.py``
    for the migration). Cross-schema FK to ``auth.users.id`` — the
    consolidation transplant relocated the users table from
    ``runner.users`` / ``public.users`` to ``auth.users`` via
    ``consolidation_phase2_zz_final_runner_cleanup``.
    """

    __tablename__ = "subscriptions"
    __table_args__ = {"schema": "cloud"}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Stripe fields
    stripe_customer_id = Column(String, nullable=True, index=True)
    stripe_subscription_id = Column(String, nullable=True, index=True)
    stripe_price_id = Column(String, nullable=True)

    # Subscription details
    tier = Column(String, default=SubscriptionTier.FREE.value, nullable=False)
    status = Column(String, default=SubscriptionStatus.ACTIVE.value, nullable=False)

    # Dates
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    canceled_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    #
    # Subscription.user is a one-way reference to qontinui-web's User model.
    # We deliberately do NOT use back_populates="subscription" here because:
    #
    # 1. qontinui-web is the OSS core and MUST be deployable without
    #    cloud-control installed (per app/main.py:18 ImportError handling).
    # 2. If User declared subscription = relationship("Subscription", ...)
    #    on its side, mapper init in the OSS-only deploy fails looking for
    #    a missing class — the AWS staging login outage on 2026-05-20.
    # 3. A one-way reference here keeps the cross-package coupling clean:
    #    cloud-control depends on web's User, never vice versa.
    user = relationship("User")
