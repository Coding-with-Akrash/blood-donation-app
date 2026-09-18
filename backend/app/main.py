from datetime import date, timedelta
from pathlib import Path
from uuid import UUID, uuid4
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.config import get_settings
from app.database import get_db
from app.deps import current_user, require_roles
from app.models import BloodProduct, BloodRequest, Donation, DonationStatus, Donor, Notification, ProductStatus, Recipient, RequestStatus, Role, User
from app.schemas import (DashboardOut, DonationIn, DonationOut, DonorIn, DonorOut, EligibilityOut, FulfillIn, LoginIn, ProductIn, ProductOut, RecipientIn, RecipientOut, RegisterIn, ReportOut, RequestIn, RequestOut, StatusIn, TokenOut, UserCreateIn, UserOut)
from app.security import create_access_token, hash_password, verify_password
from app.services import audit, donor_eligible, expire_inventory, new_notification

settings = get_settings()
app = FastAPI(title="Blood Donation Department API", version="1.0.0", docs_url="/api/docs" if settings.expose_api_docs else None, openapi_url="/api/openapi.json" if settings.expose_api_docs else None)
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_credentials=True, allow_methods=["GET", "POST", "PATCH"], allow_headers=["Authorization", "Content-Type"])
static_dir = Path(__file__).resolve().parent.parent / "static"
if (static_dir / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response


@app.exception_handler(IntegrityError)
async def integrity_error(_: Request, __: IntegrityError):
    return JSONResponse(status_code=409, content={"detail": "a record with that unique value already exists"})


@app.get("/api/health", include_in_schema=False)
def health():
    return {"status": "ok"}


@app.post("/api/auth/login", response_model=TokenOut)
def login(payload: LoginIn, request: Request, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid email or password")
    audit(db, user.id, "login", "user", str(user.id), request)
    db.commit()
    return TokenOut(access_token=create_access_token(str(user.id), user.role.value), user=user)


@app.post("/api/auth/register", response_model=TokenOut, status_code=201)
def register_donor(payload: RegisterIn, request: Request, db: Session = Depends(get_db)):
    """Self-service donor registration. Staff verify eligibility at each donation."""
    user = User(email=payload.email.lower(), password_hash=hash_password(payload.password), role=Role.DONOR)
    db.add(user); db.flush()
    donor_record = Donor(user_id=user.id, donor_code=f"D{date.today():%Y%m%d}-{str(user.id)[:6].upper()}", **payload.model_dump(exclude={"email", "password"}))
    db.add(donor_record)
    audit(db, user.id, "register", "donor", str(donor_record.id), request)
    db.commit(); db.refresh(user)
    return TokenOut(access_token=create_access_token(str(user.id), user.role.value), user=user)


@app.get("/api/users/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@app.get("/api/users", response_model=list[UserOut])
def list_users(_: User = Depends(require_roles(Role.ADMIN)), db: Session = Depends(get_db)):
    return db.scalars(select(User).order_by(User.created_at.desc()).limit(200)).all()


@app.post("/api/users", response_model=UserOut, status_code=201)
def create_user(payload: UserCreateIn, request: Request, user: User = Depends(require_roles(Role.ADMIN)), db: Session = Depends(get_db)):
    new_user = User(email=payload.email.lower(), password_hash=hash_password(payload.password), role=payload.role)
    db.add(new_user); db.flush(); audit(db, user.id, "create", "user", str(new_user.id), request, {"role": payload.role.value}); db.commit(); db.refresh(new_user)
    return new_user


@app.get("/api/notifications")
def notifications(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.scalars(select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(30)).all()


@app.get("/api/donors", response_model=list[DonorOut])
def list_donors(q: str | None = None, blood_group: str | None = None, limit: int = 50, _: User = Depends(require_roles(Role.STAFF, Role.ADMIN)), db: Session = Depends(get_db)):
    stmt = select(Donor)
    if q:
        term = f"%{q.strip()}%"
        stmt = stmt.where(or_(Donor.donor_code.ilike(term), Donor.first_name.ilike(term), Donor.last_name.ilike(term), Donor.phone.ilike(term)))
    if blood_group:
        stmt = stmt.where(Donor.blood_group == blood_group)
    return db.scalars(stmt.order_by(Donor.created_at.desc()).limit(min(limit, 100))).all()


@app.post("/api/donors", response_model=DonorOut, status_code=201)
def create_donor(payload: DonorIn, request: Request, user: User = Depends(require_roles(Role.STAFF, Role.ADMIN)), db: Session = Depends(get_db)):
    donor = Donor(donor_code=f"D{date.today():%Y%m%d}-{str(uuid4())[:6].upper()}", **payload.model_dump())
    db.add(donor); db.flush(); audit(db, user.id, "create", "donor", str(donor.id), request); db.commit(); db.refresh(donor)
    return donor


@app.get("/api/donors/me", response_model=DonorOut)
def my_donor_profile(user: User = Depends(require_roles(Role.DONOR)), db: Session = Depends(get_db)):
    donor = db.scalar(select(Donor).where(Donor.user_id == user.id))
    if not donor: raise HTTPException(404, "donor profile not found")
    return donor


@app.get("/api/donors/{donor_id}/eligibility", response_model=EligibilityOut)
def donor_eligibility(donor_id: UUID, planned_date: date = date.today(), _: User = Depends(require_roles(Role.STAFF, Role.ADMIN)), db: Session = Depends(get_db)):
    donor = db.get(Donor, donor_id)
    if not donor: raise HTTPException(404, "donor not found")
    eligible, reason = donor_eligible(donor, planned_date)
    return EligibilityOut(eligible=eligible, reason=reason)


@app.get("/api/donations", response_model=list[DonationOut])
def list_donations(donor_id: UUID | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)):
    stmt = select(Donation)
    if user.role == Role.DONOR:
        donor = db.scalar(select(Donor).where(Donor.user_id == user.id))
        if not donor: return []
        stmt = stmt.where(Donation.donor_id == donor.id)
    elif donor_id:
        stmt = stmt.where(Donation.donor_id == donor_id)
    return db.scalars(stmt.order_by(Donation.donation_date.desc()).limit(100)).all()


@app.post("/api/donations", response_model=DonationOut, status_code=201)
def create_donation(payload: DonationIn, request: Request, user: User = Depends(require_roles(Role.STAFF, Role.ADMIN)), db: Session = Depends(get_db)):
    donor = db.get(Donor, payload.donor_id)
    if not donor: raise HTTPException(404, "donor not found")
    eligible, reason = donor_eligible(donor, payload.donation_date)
    if payload.status != DonationStatus.DEFERRED and not eligible: raise HTTPException(422, reason)
    donation = Donation(**payload.model_dump())
    if payload.status == DonationStatus.COMPLETED: donor.last_donation_date = payload.donation_date
    db.add(donation); db.flush(); audit(db, user.id, "create", "donation", str(donation.id), request, {"status": payload.status.value}); db.commit(); db.refresh(donation)
    return donation


@app.get("/api/inventory", response_model=list[ProductOut])
def inventory(blood_group: str | None = None, component: str | None = None, status_filter: ProductStatus | None = None, _: User = Depends(require_roles(Role.STAFF, Role.ADMIN)), db: Session = Depends(get_db)):
    expire_inventory(db); db.commit()
    stmt = select(BloodProduct)
    if blood_group: stmt = stmt.where(BloodProduct.blood_group == blood_group)
    if component: stmt = stmt.where(BloodProduct.component == component)
    if status_filter: stmt = stmt.where(BloodProduct.status == status_filter)
    return db.scalars(stmt.order_by(BloodProduct.expires_on).limit(200)).all()


@app.post("/api/inventory", response_model=ProductOut, status_code=201)
def create_product(payload: ProductIn, request: Request, user: User = Depends(require_roles(Role.STAFF, Role.ADMIN)), db: Session = Depends(get_db)):
    donation = db.get(Donation, payload.donation_id)
    if not donation or donation.status != DonationStatus.COMPLETED: raise HTTPException(422, "products can only be created from completed donations")
    product = BloodProduct(**payload.model_dump())
    db.add(product); db.flush(); audit(db, user.id, "create", "blood_product", str(product.id), request); db.commit(); db.refresh(product)
    return product


@app.get("/api/recipients", response_model=list[RecipientOut])
def recipients(q: str | None = None, _: User = Depends(require_roles(Role.STAFF, Role.ADMIN)), db: Session = Depends(get_db)):
    stmt = select(Recipient)
    if q:
        term = f"%{q.strip()}%"; stmt = stmt.where(or_(Recipient.medical_record_number.ilike(term), Recipient.first_name.ilike(term), Recipient.last_name.ilike(term)))
    return db.scalars(stmt.order_by(Recipient.created_at.desc()).limit(100)).all()


@app.post("/api/recipients", response_model=RecipientOut, status_code=201)
def create_recipient(payload: RecipientIn, request: Request, user: User = Depends(require_roles(Role.STAFF, Role.ADMIN)), db: Session = Depends(get_db)):
    recipient = Recipient(**payload.model_dump()); db.add(recipient); db.flush(); audit(db, user.id, "create", "recipient", str(recipient.id), request); db.commit(); db.refresh(recipient)
    return recipient


@app.get("/api/requests", response_model=list[RequestOut])
def list_requests(status_filter: RequestStatus | None = None, _: User = Depends(require_roles(Role.STAFF, Role.ADMIN)), db: Session = Depends(get_db)):
    stmt = select(BloodRequest)
    if status_filter: stmt = stmt.where(BloodRequest.status == status_filter)
    return db.scalars(stmt.order_by(BloodRequest.created_at.desc()).limit(100)).all()


@app.post("/api/requests", response_model=RequestOut, status_code=201)
def create_request(payload: RequestIn, request: Request, user: User = Depends(require_roles(Role.STAFF, Role.ADMIN)), db: Session = Depends(get_db)):
    if not db.get(Recipient, payload.recipient_id): raise HTTPException(404, "recipient not found")
    record = BloodRequest(**payload.model_dump()); db.add(record); db.flush(); audit(db, user.id, "create", "blood_request", str(record.id), request); db.commit(); db.refresh(record)
    return record


@app.patch("/api/requests/{request_id}/status", response_model=RequestOut)
def update_request_status(request_id: UUID, payload: StatusIn, request: Request, user: User = Depends(require_roles(Role.STAFF, Role.ADMIN)), db: Session = Depends(get_db)):
    record = db.get(BloodRequest, request_id)
    if not record: raise HTTPException(404, "request not found")
    record.status = payload.status; audit(db, user.id, "status_change", "blood_request", str(record.id), request, {"status": payload.status.value}); db.commit(); db.refresh(record)
    return record


@app.post("/api/requests/{request_id}/fulfill", response_model=RequestOut)
def fulfill_request(request_id: UUID, payload: FulfillIn, request: Request, user: User = Depends(require_roles(Role.STAFF, Role.ADMIN)), db: Session = Depends(get_db)):
    record = db.get(BloodRequest, request_id)
    if not record: raise HTTPException(404, "request not found")
    products = db.scalars(select(BloodProduct).where(BloodProduct.id.in_(payload.product_ids)).with_for_update()).all()
    if len(products) != len(payload.product_ids) or len(products) != record.units_requested: raise HTTPException(422, "select exactly the requested number of units")
    if any(p.status != ProductStatus.AVAILABLE or p.component != record.component or p.blood_group != record.blood_group or p.expires_on < date.today() for p in products):
        raise HTTPException(422, "one or more units are unavailable or incompatible")
    for product in products: product.status = ProductStatus.ISSUED
    record.status = RequestStatus.FULFILLED
    audit(db, user.id, "fulfill", "blood_request", str(record.id), request, {"product_ids": [str(p.id) for p in products]})
    db.commit(); db.refresh(record)
    return record


@app.get("/api/dashboard", response_model=DashboardOut)
def dashboard(_: User = Depends(require_roles(Role.STAFF, Role.ADMIN)), db: Session = Depends(get_db)):
    expire_inventory(db); db.commit()
    available = db.scalar(select(func.count()).select_from(BloodProduct).where(BloodProduct.status == ProductStatus.AVAILABLE)) or 0
    expiring = db.scalar(select(func.count()).select_from(BloodProduct).where(BloodProduct.status == ProductStatus.AVAILABLE, BloodProduct.expires_on <= date.today() + timedelta(days=7))) or 0
    pending = db.scalar(select(func.count()).select_from(BloodRequest).where(BloodRequest.status.in_([RequestStatus.PENDING, RequestStatus.APPROVED]))) or 0
    donor_count = db.scalar(select(func.count()).select_from(Donor)) or 0
    groups = db.execute(select(BloodProduct.blood_group, func.count()).where(BloodProduct.status == ProductStatus.AVAILABLE).group_by(BloodProduct.blood_group)).all()
    return DashboardOut(available_units=available, expiring_soon=expiring, pending_requests=pending, donors=donor_count, inventory_by_group={group.value: count for group, count in groups})


@app.get("/api/audit")
def audit_logs(limit: int = 100, _: User = Depends(require_roles(Role.ADMIN)), db: Session = Depends(get_db)):
    from app.models import AuditLog
    return db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(min(limit, 200))).all()


@app.get("/api/reports/summary", response_model=ReportOut)
def report_summary(_: User = Depends(require_roles(Role.STAFF, Role.ADMIN)), db: Session = Depends(get_db)):
    expire_inventory(db); db.commit()
    completed = db.scalar(select(func.count()).select_from(Donation).where(Donation.status == DonationStatus.COMPLETED)) or 0
    deferred = db.scalar(select(func.count()).select_from(Donation).where(Donation.status == DonationStatus.DEFERRED)) or 0
    issued = db.scalar(select(func.count()).select_from(BloodProduct).where(BloodProduct.status == ProductStatus.ISSUED)) or 0
    available = db.scalar(select(func.count()).select_from(BloodProduct).where(BloodProduct.status == ProductStatus.AVAILABLE)) or 0
    return ReportOut(completed_donations=completed, deferred_donations=deferred, issued_units=issued, available_units=available)


@app.get("/{full_path:path}", include_in_schema=False)
def frontend(full_path: str):
    """Serve the compiled React single-page application in the Render image."""
    index = static_dir / "index.html"
    if index.is_file() and not full_path.startswith("api/"):
        return FileResponse(index)
    raise HTTPException(404, "not found")
