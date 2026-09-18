from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.models import BloodGroup, DonationStatus, ProductStatus, RequestStatus, Role


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    date_of_birth: date
    blood_group: BloodGroup
    phone: str = Field(min_length=7, max_length=32)
    address: str | None = Field(default=None, max_length=1000)

    @field_validator("date_of_birth")
    @classmethod
    def birth_not_future(cls, value: date) -> date:
        if value >= date.today():
            raise ValueError("date of birth must be in the past")
        return value


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(APIModel):
    id: UUID
    email: EmailStr
    role: Role
    is_active: bool


class UserCreateIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    role: Role


class EligibilityOut(BaseModel):
    eligible: bool
    reason: str | None


class DonorIn(BaseModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    date_of_birth: date
    blood_group: BloodGroup
    phone: str = Field(min_length=7, max_length=32)
    address: str | None = Field(default=None, max_length=1000)
    eligibility_notes: str | None = Field(default=None, max_length=2000)

    @field_validator("date_of_birth")
    @classmethod
    def birth_not_future(cls, value: date) -> date:
        if value >= date.today():
            raise ValueError("date of birth must be in the past")
        return value


class DonorOut(APIModel):
    id: UUID
    donor_code: str
    first_name: str
    last_name: str
    date_of_birth: date
    blood_group: BloodGroup
    phone: str
    address: str | None
    last_donation_date: date | None
    eligibility_notes: str | None
    is_deferred: bool


class DonationIn(BaseModel):
    donor_id: UUID
    donation_date: date
    volume_ml: int = Field(ge=250, le=550)
    hemoglobin_g_dl: float | None = Field(default=None, ge=5, le=25)
    blood_pressure: str | None = Field(default=None, max_length=20)
    status: DonationStatus = DonationStatus.SCHEDULED
    deferral_reason: str | None = Field(default=None, max_length=2000)
    screening_notes: str | None = Field(default=None, max_length=4000)


class DonationOut(APIModel):
    id: UUID
    donor_id: UUID
    donation_date: date
    volume_ml: int
    hemoglobin_g_dl: float | None
    status: DonationStatus
    deferral_reason: str | None


class ProductIn(BaseModel):
    donation_id: UUID
    unit_code: str = Field(pattern=r"^[A-Za-z0-9-]{4,32}$")
    component: str = Field(pattern=r"^(whole_blood|red_cells|plasma|platelets)$")
    blood_group: BloodGroup
    volume_ml: int = Field(gt=0, le=1000)
    collected_on: date
    expires_on: date

    @field_validator("expires_on")
    @classmethod
    def expiry_after_collection(cls, value: date, info):
        if info.data.get("collected_on") and value <= info.data["collected_on"]:
            raise ValueError("expiry must be after collection")
        return value


class ProductOut(APIModel):
    id: UUID
    donation_id: UUID
    unit_code: str
    component: str
    blood_group: BloodGroup
    volume_ml: int
    collected_on: date
    expires_on: date
    status: ProductStatus


class RecipientIn(BaseModel):
    medical_record_number: str = Field(min_length=3, max_length=50)
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    blood_group: BloodGroup
    phone: str | None = Field(default=None, max_length=32)


class RecipientOut(APIModel):
    id: UUID
    medical_record_number: str
    first_name: str
    last_name: str
    blood_group: BloodGroup
    phone: str | None


class RequestIn(BaseModel):
    recipient_id: UUID
    component: str = Field(pattern=r"^(whole_blood|red_cells|plasma|platelets)$")
    blood_group: BloodGroup
    units_requested: int = Field(gt=0, le=20)
    priority: str = Field(default="routine", pattern=r"^(routine|urgent|emergency)$")
    needed_by: datetime | None = None
    notes: str | None = Field(default=None, max_length=2000)


class RequestOut(APIModel):
    id: UUID
    recipient_id: UUID
    component: str
    blood_group: BloodGroup
    units_requested: int
    priority: str
    needed_by: datetime | None
    status: RequestStatus
    notes: str | None


class StatusIn(BaseModel):
    status: RequestStatus


class FulfillIn(BaseModel):
    product_ids: list[UUID] = Field(min_length=1, max_length=20)


class DashboardOut(BaseModel):
    available_units: int
    expiring_soon: int
    pending_requests: int
    donors: int
    inventory_by_group: dict[str, int]


class ReportOut(BaseModel):
    completed_donations: int
    deferred_donations: int
    issued_units: int
    available_units: int


TokenOut.model_rebuild()
