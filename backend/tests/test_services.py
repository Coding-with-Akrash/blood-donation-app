from datetime import date, timedelta
from app.models import Donor
from app.services import donor_eligible


def test_donor_eligibility_enforces_interval():
    donor = Donor(donor_code="D-1", first_name="Ada", last_name="Lovelace", date_of_birth=date(1990, 1, 1), blood_group="O+", phone="1234567", last_donation_date=date.today())
    eligible, reason = donor_eligible(donor, date.today() + timedelta(days=55))
    assert not eligible
    assert "56-day" in reason


def test_deferred_donor_is_not_eligible():
    donor = Donor(donor_code="D-2", first_name="Grace", last_name="Hopper", date_of_birth=date(1990, 1, 1), blood_group="A+", phone="1234567", is_deferred=True)
    eligible, _ = donor_eligible(donor, date.today())
    assert not eligible
