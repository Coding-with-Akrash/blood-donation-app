from datetime import date, timedelta
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models import AuditLog, BloodProduct, Donation, Donor, Notification, ProductStatus


def audit(db: Session, actor_id, action: str, entity_type: str, entity_id: str, request=None, metadata: dict | None = None) -> None:
    ip = request.client.host if request and request.client else None
    db.add(AuditLog(actor_id=actor_id, action=action, entity_type=entity_type, entity_id=str(entity_id), metadata_=metadata or {}, ip_address=ip))


def donor_eligible(donor: Donor, planned_date: date) -> tuple[bool, str | None]:
    if donor.is_deferred:
        return False, "donor is currently deferred"
    if donor.last_donation_date and planned_date < donor.last_donation_date + timedelta(days=56):
        return False, "minimum 56-day donation interval has not elapsed"
    return True, None


def expire_inventory(db: Session) -> None:
    db.query(BloodProduct).filter(BloodProduct.expires_on < date.today(), BloodProduct.status == ProductStatus.AVAILABLE).update({BloodProduct.status: ProductStatus.EXPIRED})


def new_notification(db: Session, user_id, title: str, body: str) -> None:
    db.add(Notification(user_id=user_id, title=title, body=body))
