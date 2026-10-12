from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from app.models import Tenant


def tenant_local_date(
    tenant: Tenant,
    value: datetime | None = None,
) -> date:
    """Return an instant's calendar date in the tenant's timezone.

    Naive timestamps retain the API's established interpretation as UTC.
    """
    instant = value or datetime.now(timezone.utc)
    if instant.tzinfo is None or instant.utcoffset() is None:
        instant = instant.replace(tzinfo=timezone.utc)
    return instant.astimezone(ZoneInfo(tenant.timezone_name)).date()
