import enum
import uuid
from datetime import date, datetime
from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Role(str, enum.Enum):
    DONOR = "donor"
    STAFF = "staff"
    ADMIN = "admin"


class BloodGroup(str, enum.Enum):
    A_POS = "A+"; A_NEG = "A-"; B_POS = "B+"; B_NEG = "B-"
    AB_POS = "AB+"; AB_NEG = "AB-"; O_POS = "O+"; O_NEG = "O-"


class DonationStatus(str, enum.Enum):
    SCHEDULED = "scheduled"; COMPLETED = "completed"; DEFERRED = "deferred"; DISCARDED = "discarded"


class RequestStatus(str, enum.Enum):
    PENDING = "pending"; APPROVED = "approved"; FULFILLED = "fulfilled"; CANCELLED = "cancelled"


class ProductStatus(str, enum.Enum):
    AVAILABLE = "available"; RESERVED = "reserved"; ISSUED = "issued"; EXPIRED = "expired"; DISCARDED = "discarded"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class User(TimestampMixin, Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role, name="role"), nullable=False, default=Role.DONOR)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    donor: Mapped["Donor | None"] = relationship(back_populates="user", uselist=False)


class Donor(TimestampMixin, Base):
    __tablename__ = "donors"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), unique=True)
    donor_code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    blood_group: Mapped[BloodGroup] = mapped_column(Enum(BloodGroup, name="blood_group"), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    address: Mapped[str | None] = mapped_column(Text)
    last_donation_date: Mapped[date | None] = mapped_column(Date)
    eligibility_notes: Mapped[str | None] = mapped_column(Text)
    is_deferred: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    user: Mapped[User | None] = relationship(back_populates="donor")
    donations: Mapped[list["Donation"]] = relationship(back_populates="donor")


class Donation(TimestampMixin, Base):
    __tablename__ = "donations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    donor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("donors.id"), index=True, nullable=False)
    donation_date: Mapped[date] = mapped_column(Date, nullable=False)
    volume_ml: Mapped[int] = mapped_column(Integer, nullable=False)
    hemoglobin_g_dl: Mapped[float | None] = mapped_column(Numeric(4, 1))
    blood_pressure: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[DonationStatus] = mapped_column(Enum(DonationStatus, name="donation_status"), default=DonationStatus.SCHEDULED, nullable=False)
    deferral_reason: Mapped[str | None] = mapped_column(Text)
    screening_notes: Mapped[str | None] = mapped_column(Text)
    donor: Mapped[Donor] = relationship(back_populates="donations")
    products: Mapped[list["BloodProduct"]] = relationship(back_populates="donation")
    __table_args__ = (CheckConstraint("volume_ml BETWEEN 250 AND 550", name="valid_donation_volume"),)


class BloodProduct(TimestampMixin, Base):
    __tablename__ = "blood_products"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    donation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("donations.id"), index=True, nullable=False)
    unit_code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    component: Mapped[str] = mapped_column(String(40), nullable=False)
    blood_group: Mapped[BloodGroup] = mapped_column(Enum(BloodGroup, name="blood_group"), nullable=False)
    volume_ml: Mapped[int] = mapped_column(Integer, nullable=False)
    collected_on: Mapped[date] = mapped_column(Date, nullable=False)
    expires_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[ProductStatus] = mapped_column(Enum(ProductStatus, name="product_status"), default=ProductStatus.AVAILABLE, nullable=False, index=True)
    donation: Mapped[Donation] = relationship(back_populates="products")
    __table_args__ = (CheckConstraint("volume_ml > 0", name="positive_product_volume"),)


class Recipient(TimestampMixin, Base):
    __tablename__ = "recipients"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    medical_record_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)
    blood_group: Mapped[BloodGroup] = mapped_column(Enum(BloodGroup, name="blood_group"), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32))


class BloodRequest(TimestampMixin, Base):
    __tablename__ = "blood_requests"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("recipients.id"), nullable=False, index=True)
    component: Mapped[str] = mapped_column(String(40), nullable=False)
    blood_group: Mapped[BloodGroup] = mapped_column(Enum(BloodGroup, name="blood_group"), nullable=False)
    units_requested: Mapped[int] = mapped_column(Integer, nullable=False)
    priority: Mapped[str] = mapped_column(String(16), default="routine", nullable=False)
    needed_by: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[RequestStatus] = mapped_column(Enum(RequestStatus, name="request_status"), default=RequestStatus.PENDING, nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (CheckConstraint("units_requested > 0", name="positive_units_requested"),)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


class Notification(TimestampMixin, Base):
    __tablename__ = "notifications"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
