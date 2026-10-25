from datetime import date, datetime, timezone, timedelta
from backend.src.schemas.base import ApiSchema


class TimestampResponse(ApiSchema):
    created_at: datetime
    registration_date: date


def test_utc_serialization_is_identical_after_sqlite_timezone_loss():
    aware = datetime(2026, 10, 25, 12, 30, tzinfo=timezone.utc)
    naive = aware.replace(tzinfo=None)
    values = dict(registration_date=date(2020, 1, 1))
    original = TimestampResponse(created_at=aware, **values).model_dump(mode='json')
    reloaded = TimestampResponse(created_at=naive, **values).model_dump(mode='json')
    assert original == reloaded
    assert original['createdAt'].endswith('Z')
    assert original['registrationDate'] == '2020-01-01'


def test_aware_offsets_are_converted_without_changing_the_instant():
    stamp = datetime(2026, 10, 25, 15, 30, tzinfo=timezone(timedelta(hours=3)))
    result = TimestampResponse(created_at=stamp, registration_date=date(2020, 1, 1))
    assert result.model_dump(mode='json')['createdAt'] == '2026-10-25T12:30:00Z'
