"""
Database models for GrandmaScraper.

Models:
- User: Application users
- ScrapeJobDB: Scraping job configurations
- ScrapeResultDB: Scraping results
- Schedule: Job scheduling information
- Webhook: Webhook configurations for notifications
- WebhookDelivery: Webhook delivery tracking

All models include comprehensive indexes for query performance optimization.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import String, Boolean, DateTime, Text, Integer, ForeignKey, JSON, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from grandma_scraper.db.base import Base


class UserRole(str, enum.Enum):
    """User roles for access control."""

    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"


class JobStatus(str, enum.Enum):
    """Status of a scrape job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class User(Base):
    """
    User model for authentication and authorization.

    Attributes:
        id: Unique user ID (UUID)
        email: User email (unique, login identifier)
        username: Display name
        hashed_password: Bcrypt hashed password
        is_active: Whether user account is active
        is_superuser: Whether user has admin privileges
        role: User role (admin, user, readonly)
        created_at: Account creation timestamp
        updated_at: Last update timestamp
        jobs: Relationship to user's scrape jobs
    """

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole), default=UserRole.USER, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    jobs: Mapped[list["ScrapeJobDB"]] = relationship(
        "ScrapeJobDB", back_populates="owner", cascade="all, delete-orphan"
    )
    webhooks: Mapped[list["Webhook"]] = relationship(
        "Webhook", back_populates="owner", cascade="all, delete-orphan"
    )

    # Indexes for common queries
    __table_args__ = (
        Index('idx_user_email_active', 'email', 'is_active'),
        Index('idx_user_role', 'role'),
        Index('idx_user_active', 'is_active'),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"


class ScrapeJobDB(Base):
    """
    Scrape job configuration stored in database.

    Attributes:
        id: Unique job ID (UUID)
        name: Job name
        description: Job description
        config: Full job configuration (JSON - stores ScrapeJob model as dict)
        enabled: Whether job is active
        owner_id: User who created this job
        created_at: Job creation timestamp
        updated_at: Last update timestamp
        results: Relationship to job results
        schedules: Relationship to job schedules
        owner: Relationship to owning user
    """

    __tablename__ = "scrapejobdb"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Store full ScrapeJob configuration as JSON
    config: Mapped[dict] = mapped_column(JSON, nullable=False)

    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Ownership
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    owner: Mapped[User] = relationship("User", back_populates="jobs")
    results: Mapped[list["ScrapeResultDB"]] = relationship(
        "ScrapeResultDB", back_populates="job", cascade="all, delete-orphan"
    )
    schedules: Mapped[list["Schedule"]] = relationship(
        "Schedule", back_populates="job", cascade="all, delete-orphan"
    )

    # Indexes for common queries
    __table_args__ = (
        Index('idx_job_owner_enabled', 'owner_id', 'enabled'),
        Index('idx_job_enabled', 'enabled'),
        Index('idx_job_created', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<ScrapeJobDB(id={self.id}, name={self.name})>"


class ScrapeResultDB(Base):
    """
    Scrape result stored in database.

    Attributes:
        id: Unique result ID (UUID)
        job_id: Foreign key to ScrapeJobDB
        run_id: Unique ID for this execution run
        status: Execution status (pending, running, completed, failed, cancelled)
        items: Scraped data items (JSON array)
        total_items: Count of items collected
        pages_scraped: Number of pages processed
        started_at: When scraping started
        completed_at: When scraping finished
        duration_seconds: Execution duration
        error_message: Error message if failed
        error_details: Detailed error information (JSON)
        warnings: List of warnings (JSON array)
        created_at: Result creation timestamp
        job: Relationship to parent job
    """

    __tablename__ = "scraperesultdb"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    job_id: Mapped[UUID] = mapped_column(ForeignKey("scrapejobdb.id"), nullable=False, index=True)
    run_id: Mapped[UUID] = mapped_column(default=uuid4, nullable=False, index=True)

    status: Mapped[JobStatus] = mapped_column(
        SQLEnum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True
    )

    # Results
    items: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    total_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pages_scraped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(nullable=True)

    # Errors
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Warnings
    warnings: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    job: Mapped[ScrapeJobDB] = relationship("ScrapeJobDB", back_populates="results")
    webhook_deliveries: Mapped[list["WebhookDelivery"]] = relationship(
        "WebhookDelivery", back_populates="result", cascade="all, delete-orphan"
    )

    # Indexes for common queries
    __table_args__ = (
        Index('idx_result_job_status', 'job_id', 'status'),
        Index('idx_result_run_id', 'run_id'),
        Index('idx_result_created', 'created_at'),
        Index('idx_result_status_created', 'status', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<ScrapeResultDB(id={self.id}, status={self.status})>"


class Schedule(Base):
    """
    Job schedule configuration.

    Attributes:
        id: Unique schedule ID (UUID)
        job_id: Foreign key to ScrapeJobDB
        enabled: Whether schedule is active
        cron_expression: Cron expression for scheduling
        next_run: Next scheduled run time
        last_run: Last actual run time
        timezone: Timezone for schedule (default: UTC)
        created_at: Schedule creation timestamp
        updated_at: Last update timestamp
        job: Relationship to parent job
    """

    __tablename__ = "schedule"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    job_id: Mapped[UUID] = mapped_column(ForeignKey("scrapejobdb.id"), nullable=False, index=True)

    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Cron expression (e.g., "0 0 * * *" for daily at midnight)
    cron_expression: Mapped[str] = mapped_column(String(100), nullable=False)

    # Schedule tracking
    next_run: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    last_run: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timezone (IANA timezone string, e.g., "America/New_York")
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    job: Mapped[ScrapeJobDB] = relationship("ScrapeJobDB", back_populates="schedules")

    # Indexes for common queries
    __table_args__ = (
        Index('idx_schedule_enabled_next_run', 'enabled', 'next_run'),
        Index('idx_schedule_next_run', 'next_run'),
    )

    def __repr__(self) -> str:
        return f"<Schedule(id={self.id}, cron={self.cron_expression})>"


class WebhookEventType(str, enum.Enum):
    """Webhook event types."""

    JOB_COMPLETED = "job.completed"
    JOB_FAILED = "job.failed"
    JOB_STARTED = "job.started"
    JOB_CANCELLED = "job.cancelled"


class Webhook(Base):
    """
    Webhook configuration for job notifications.

    Attributes:
        id: Unique webhook ID (UUID)
        owner_id: User who created this webhook
        name: Webhook name/label
        url: Webhook destination URL
        enabled: Whether webhook is active
        events: List of events to trigger on (JSON array)
        secret: Optional secret for webhook signature verification
        headers: Optional custom headers (JSON dict)
        retry_on_failure: Whether to retry failed deliveries
        max_retries: Maximum retry attempts
        created_at: Webhook creation timestamp
        updated_at: Last update timestamp
        owner: Relationship to owning user
        deliveries: Relationship to webhook deliveries
    """

    __tablename__ = "webhook"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Events to trigger on
    events: Mapped[list] = mapped_column(JSON, nullable=False)

    # Security
    secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Custom headers (JSON dict)
    headers: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Retry configuration
    retry_on_failure: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    owner: Mapped[User] = relationship("User", back_populates="webhooks")
    deliveries: Mapped[list["WebhookDelivery"]] = relationship(
        "WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index('idx_webhook_owner_enabled', 'owner_id', 'enabled'),
        Index('idx_webhook_enabled', 'enabled'),
    )

    def __repr__(self) -> str:
        return f"<Webhook(id={self.id}, url={self.url})>"


class WebhookDeliveryStatus(str, enum.Enum):
    """Webhook delivery status."""

    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


class WebhookDelivery(Base):
    """
    Webhook delivery attempt record.

    Attributes:
        id: Unique delivery ID (UUID)
        webhook_id: Foreign key to Webhook
        result_id: Foreign key to ScrapeResultDB
        event_type: Event that triggered the webhook
        status: Delivery status
        payload: Webhook payload sent (JSON)
        response_status: HTTP status code from webhook endpoint
        response_body: Response body (truncated)
        error_message: Error message if failed
        attempts: Number of delivery attempts
        next_retry: Next retry time if applicable
        delivered_at: When successfully delivered
        created_at: Delivery creation timestamp
        webhook: Relationship to webhook configuration
        result: Relationship to scrape result
    """

    __tablename__ = "webhook_delivery"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    webhook_id: Mapped[UUID] = mapped_column(ForeignKey("webhook.id"), nullable=False, index=True)
    result_id: Mapped[UUID] = mapped_column(ForeignKey("scraperesultdb.id"), nullable=False, index=True)

    event_type: Mapped[WebhookEventType] = mapped_column(
        SQLEnum(WebhookEventType), nullable=False
    )

    status: Mapped[WebhookDeliveryStatus] = mapped_column(
        SQLEnum(WebhookDeliveryStatus), default=WebhookDeliveryStatus.PENDING, nullable=False
    )

    # Payload and response
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    response_status: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Retry tracking
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    next_retry: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    webhook: Mapped[Webhook] = relationship("Webhook", back_populates="deliveries")
    result: Mapped[ScrapeResultDB] = relationship("ScrapeResultDB", back_populates="webhook_deliveries")

    # Indexes
    __table_args__ = (
        Index('idx_delivery_webhook_status', 'webhook_id', 'status'),
        Index('idx_delivery_status_next_retry', 'status', 'next_retry'),
        Index('idx_delivery_created', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<WebhookDelivery(id={self.id}, status={self.status})>"
