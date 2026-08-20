from fastapi import APIRouter


router = APIRouter(
    prefix="/status",
    tags=["PermitPulse"],
)


@router.get("")
def permitpulse_status():
    return {
        "product": "permitpulse",
        "status": "available",
    }
