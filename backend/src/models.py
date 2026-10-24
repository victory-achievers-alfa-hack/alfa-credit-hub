from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.src.database import Base
from backend.src.scoring.financing import POLICY_VERSION


SCORING_POLICY_VERSION = POLICY_VERSION


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_public_id() -> str:
    return str(uuid4())


class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (
        CheckConstraint("length(inn) IN (10, 12)", name="ck_companies_inn_length"),
        CheckConstraint(
            "monthly_revenue >= 0", name="ck_companies_revenue_nonnegative"
        ),
        CheckConstraint(
            "monthly_expenses >= 0", name="ck_companies_expenses_nonnegative"
        ),
        CheckConstraint(
            "current_monthly_debt_payment >= 0", name="ck_companies_debt_nonnegative"
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    legal_name: Mapped[str] = mapped_column(String(150), nullable=False)
    representative: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    inn: Mapped[str] = mapped_column(
        String(12), unique=True, nullable=False, index=True
    )
    okved: Mapped[str] = mapped_column(String(120), nullable=False)
    sector: Mapped[str] = mapped_column(String(100), nullable=False)
    account: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    registration_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    monthly_revenue: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    monthly_expenses: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    current_monthly_debt_payment: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False
    )
    has_overdue: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    scoring_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    turnover: Mapped[list[float]] = mapped_column(JSON, nullable=False, default=list)

    @property
    def active(self) -> bool:
        return self.status == "active"

    users: Mapped[list["User"]] = relationship(back_populates="company")
    documents: Mapped[list["CompanyDocument"]] = relationship(
        back_populates="company", cascade="all, delete-orphan", passive_deletes=True
    )
    applications: Mapped[list["Application"]] = relationship(
        back_populates="company", cascade="all, delete-orphan", passive_deletes=True
    )


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "(role = 'bank' AND company_id IS NULL) OR "
            "(role = 'client' AND company_id IS NOT NULL)",
            name="ck_users_role_company",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, default=new_public_id
    )
    email: Mapped[str] = mapped_column(
        String(254), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    contact_name: Mapped[str] = mapped_column(String(120), nullable=False)
    initials: Mapped[str] = mapped_column(String(8), nullable=False)
    company_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("companies.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    company: Mapped["Company | None"] = relationship(back_populates="users")
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    application_events: Mapped[list["ApplicationEvent"]] = relationship(
        back_populates="actor"
    )
    decisions: Mapped[list["OfferDecision"]] = relationship(back_populates="actor")


class CreditProduct(Base):
    __tablename__ = "credit_products"
    __table_args__ = (
        CheckConstraint(
            "min_amount > 0", name="ck_credit_products_min_amount_positive"
        ),
        CheckConstraint(
            "max_amount >= min_amount", name="ck_credit_products_amount_range"
        ),
        CheckConstraint(
            "rate >= 0 AND rate <= 100", name="ck_credit_products_rate_range"
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    short_name: Mapped[str] = mapped_column(String(127), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    purposes: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    min_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    max_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    terms: Mapped[list[int]] = mapped_column(JSON, nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    accent: Mapped[str] = mapped_column(String(16), nullable=False, default="#e7e9ff")
    icon: Mapped[str] = mapped_column(String(32), nullable=False, default="wallet")

    applications: Mapped[list["Application"]] = relationship(back_populates="product")


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_applications_amount_positive"),
        CheckConstraint("term_months > 0", name="ck_applications_term_positive"),
        CheckConstraint(
            "status IN ('review', 'need_info', 'offer', 'sign', 'ready', 'disbursed', 'rejected')",
            name="ck_applications_status",
        ),
        CheckConstraint(
            "purpose IN ('goods', 'equipment', 'cash_gap')",
            name="ck_applications_purpose",
        ),
        UniqueConstraint("id", "company_id", name="uq_applications_id_company"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("credit_products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    purpose: Mapped[str] = mapped_column(String(32), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    term_months: Mapped[int] = mapped_column(Integer, nullable=False)
    requested_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="review", index=True
    )
    bank_comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
        index=True,
    )

    company: Mapped["Company"] = relationship(back_populates="applications")
    product: Mapped["CreditProduct"] = relationship(back_populates="applications")
    creator: Mapped["User"] = relationship(foreign_keys=[created_by_user_id])
    events: Mapped[list["ApplicationEvent"]] = relationship(
        back_populates="application",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ApplicationEvent.created_at",
    )
    assessments: Mapped[list["ApplicationCheck"]] = relationship(
        back_populates="application",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ApplicationCheck.created_at",
    )
    decisions: Mapped[list["OfferDecision"]] = relationship(
        back_populates="application", cascade="all, delete-orphan", passive_deletes=True
    )
    document_links: Mapped[list["ApplicationDocument"]] = relationship(
        back_populates="application", cascade="all, delete-orphan", passive_deletes=True
    )


class CompanyDocument(Base):
    __tablename__ = "company_documents"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'ready', 'attention', 'verified', 'rejected')",
            name="ck_company_documents_status",
        ),
        UniqueConstraint("id", "company_id", name="uq_company_documents_id_company"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_public_id)
    company_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    source: Mapped[str | None] = mapped_column(String(64))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    company: Mapped["Company"] = relationship(back_populates="documents")
    application_links: Mapped[list["ApplicationDocument"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", passive_deletes=True
    )


class ApplicationDocument(Base):
    __tablename__ = "application_documents"
    __table_args__ = (
        ForeignKeyConstraint(
            ["application_id", "company_id"],
            ["applications.id", "applications.company_id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["document_id", "company_id"],
            ["company_documents.id", "company_documents.company_id"],
            ondelete="CASCADE",
        ),
    )

    application_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    attached_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    attached_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    application: Mapped["Application"] = relationship(back_populates="document_links")
    document: Mapped["CompanyDocument"] = relationship(
        back_populates="application_links"
    )
    attached_by: Mapped["User"] = relationship()


class ApplicationEvent(Base):
    __tablename__ = "application_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_public_id)
    application_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    old_status: Mapped[str | None] = mapped_column(String(32))
    new_status: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    actor_role: Mapped[str | None] = mapped_column(String(20))
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    application: Mapped["Application"] = relationship(back_populates="events")
    actor: Mapped["User | None"] = relationship(back_populates="application_events")


class ApplicationCheck(Base):
    """Immutable assessment snapshot; keep prior rows when inputs are recalculated."""

    __tablename__ = "application_checks"
    __table_args__ = (
        CheckConstraint(
            "score >= 0 AND score <= 100", name="ck_application_checks_score"
        ),
        CheckConstraint("monthly_payment >= 0", name="ck_application_checks_payment"),
        CheckConstraint(
            "max_available_amount >= 0", name="ck_application_checks_max_amount"
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_public_id)
    application_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rules_version: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("scoring_rules.version", ondelete="RESTRICT"),
        nullable=False,
        default=SCORING_POLICY_VERSION,
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk: Mapped[str] = mapped_column(String(16), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    coverage: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    monthly_payment: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    max_available_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False
    )
    eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    input_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    factors: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    checks: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    application: Mapped["Application"] = relationship(back_populates="assessments")
    rule: Mapped["ScoringRule"] = relationship(back_populates="assessments")


class OfferDecision(Base):
    __tablename__ = "offer_decisions"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('approve', 'alternative', 'need_info', 'reject')",
            name="ck_offer_decisions_kind",
        ),
        CheckConstraint(
            "kind NOT IN ('approve', 'alternative') OR "
            "(amount IS NOT NULL AND rate IS NOT NULL AND term_months IS NOT NULL)",
            name="ck_offer_decisions_offer_terms",
        ),
        CheckConstraint(
            "kind NOT IN ('alternative', 'need_info', 'reject') OR "
            "(comment IS NOT NULL AND length(trim(comment)) > 0)",
            name="ck_offer_decisions_comment",
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_public_id)
    application_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    term_months: Mapped[int | None] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    application: Mapped["Application"] = relationship(back_populates="decisions")
    actor: Mapped["User"] = relationship(back_populates="decisions")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_public_id)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[str | None] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True
    )
    application_id: Mapped[str | None] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=True, index=True
    )
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    user: Mapped["User"] = relationship(back_populates="notifications")


class ScoringRule(Base):
    __tablename__ = "scoring_rules"
    __table_args__ = (
        CheckConstraint(
            "min_score BETWEEN 0 AND 100", name="ck_scoring_rules_min_score"
        ),
        CheckConstraint("min_coverage > 0", name="ck_scoring_rules_min_coverage"),
    )

    version: Mapped[str] = mapped_column(String(32), primary_key=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    min_score: Mapped[int] = mapped_column(Integer, nullable=False, default=70)
    min_coverage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("1.25")
    )
    parameters: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    assessments: Mapped[list["ApplicationCheck"]] = relationship(back_populates="rule")
