from datetime import date, timedelta
from sqlalchemy import select
from app.config import get_settings
from app.database import SessionLocal
from app.models import BloodGroup, BloodProduct, Donation, DonationStatus, Donor, ProductStatus, Recipient, Role, User
from app.security import hash_password


def main():
    settings = get_settings()
    with SessionLocal() as db:
        existing = db.scalar(select(User).where(User.email == settings.admin_email.lower()))
        if existing:
            print("Administrator already exists")
        else:
            db.add(User(email=settings.admin_email.lower(), password_hash=hash_password(settings.admin_password), role=Role.ADMIN))
            db.commit()
            print("Administrator created")
        if settings.seed_demo_data:
            seed_demo_data(db)


def seed_demo_data(db):
    """Anonymized fixture data. Never enable this flag in a clinical deployment."""
    if db.scalar(select(Donor).where(Donor.donor_code == "DEMO-0001")):
        print("Demo data already exists")
        return
    donor = Donor(donor_code="DEMO-0001", first_name="Sample", last_name="Donor", date_of_birth=date(1990, 1, 1), blood_group=BloodGroup.O_POS, phone="0000000000", last_donation_date=date.today())
    recipient = Recipient(medical_record_number="DEMO-MRN-1", first_name="Sample", last_name="Recipient", blood_group=BloodGroup.O_POS, phone="0000000000")
    db.add_all([donor, recipient]); db.flush()
    donation = Donation(donor_id=donor.id, donation_date=date.today(), volume_ml=450, status=DonationStatus.COMPLETED)
    db.add(donation); db.flush()
    db.add(BloodProduct(donation_id=donation.id, unit_code="DEMO-UNIT-001", component="red_cells", blood_group=BloodGroup.O_POS, volume_ml=300, collected_on=date.today(), expires_on=date.today() + timedelta(days=35), status=ProductStatus.AVAILABLE))
    db.commit()
    print("Anonymized demo data created")


if __name__ == "__main__":
    main()
