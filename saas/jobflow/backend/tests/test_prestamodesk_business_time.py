from datetime import date, datetime, timezone
from types import SimpleNamespace

from app.products.prestamodesk.business_time import tenant_local_date


def test_santo_domingo_date_conversion_across_utc_midnight():
    tenant = SimpleNamespace(
        timezone_name="America/Santo_Domingo",
    )

    # 8:30 p.m. in Santo Domingo is already the next UTC calendar day.
    assert tenant_local_date(
        tenant,
        datetime(2026, 10, 11, 0, 30, tzinfo=timezone.utc),
    ) == date(2026, 10, 10)
    assert tenant_local_date(
        tenant,
        datetime(2026, 10, 11, 3, 59, tzinfo=timezone.utc),
    ) == date(2026, 10, 10)
    assert tenant_local_date(
        tenant,
        datetime(2026, 10, 11, 4, 0, tzinfo=timezone.utc),
    ) == date(2026, 10, 11)


def test_naive_api_datetime_keeps_utc_interpretation():
    tenant = SimpleNamespace(
        timezone_name="America/Santo_Domingo",
    )

    assert tenant_local_date(
        tenant,
        datetime(2026, 10, 11, 0, 30),
    ) == date(2026, 10, 10)
