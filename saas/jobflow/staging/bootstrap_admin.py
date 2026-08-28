"""Create one synthetic administrator in a new staging-only database."""
import os
import sys
from getpass import getpass

sys.path.insert(0, '/app')
from sqlalchemy import func, select, text
from sqlalchemy.engine import make_url

if os.environ.get('FIELDLOOKERS_STAGING_ONLY') != '1':
    raise SystemExit('Refusing: staging-only flag missing.')
url = make_url(os.environ.get('DATABASE_URL', ''))
if (url.host, url.database, url.username, url.port) != (
    'staging-db', 'fieldlookers_staging', 'staging_user', 5432
):
    raise SystemExit('Refusing: database is not the isolated staging target.')

# Register all product models without invoking application startup.
import app.main
from app.database import SessionLocal
from app.models import User
from app.security import hash_password

with SessionLocal() as db:
    if db.scalar(text('SELECT current_database()')) != 'fieldlookers_staging':
        raise SystemExit('Refusing: connected database name mismatch.')
    if db.scalar(select(func.count()).select_from(User)) != 0:
        raise SystemExit('Refusing: database already contains users. No user changed.')
    password = getpass('New staging-only administrator password (16+ characters): ')
    if len(password) < 16:
        raise SystemExit('Use at least 16 characters; do not reuse a real password.')
    if password != getpass('Confirm staging password: '):
        raise SystemExit('Passwords do not match.')
    db.add(User(
        email='operator@staging.example.test',
        display_name='STAGING Operator',
        password_hash=hash_password(password),
        is_active=True,
        is_platform_admin=True,
    ))
    db.commit()
print('Created operator@staging.example.test in staging only.')
