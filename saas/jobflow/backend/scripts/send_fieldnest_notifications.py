"""Inspect and recover the FieldNest outbox. Run inside the configured API container."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import update
from app.database import SessionLocal
from app.products.fieldnest.models import FieldNestNotification
from app.products.fieldnest.notifications import deliver_one, notification_counts


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--status", action="store_true")
    group.add_argument("--once", action="store_true")
    group.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--tenant-id", type=int)
    args = parser.parse_args()
    if args.retry_failed:
        if not args.tenant_id or args.tenant_id < 1:
            parser.error("--retry-failed requires a positive --tenant-id")
        with SessionLocal() as db:
            result = db.execute(update(FieldNestNotification).where(
                FieldNestNotification.tenant_id == args.tenant_id,
                FieldNestNotification.status == "failed",
            ).values(status="pending", attempts=0, last_error=None, available_at=datetime.now(timezone.utc)))
            db.commit()
            print("Requeued failed messages:", result.rowcount)
    elif args.once:
        delivered = 0
        for _ in range(20):
            if not deliver_one():
                break
            delivered += 1
        print("Processed due messages:", delivered)
    with SessionLocal() as db:
        print(json.dumps(notification_counts(db), sort_keys=True))


if __name__ == "__main__":
    main()
