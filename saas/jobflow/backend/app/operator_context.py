from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth_context import get_current_user_id
from app.database import get_db
from app.models import User


def get_current_operator(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> User:
    user = db.get(User, user_id)

    if (
        user is None
        or not user.is_active
        or not user.is_platform_admin
    ):
        raise HTTPException(
            status_code=403,
            detail="Platform operator access required",
        )

    return user
