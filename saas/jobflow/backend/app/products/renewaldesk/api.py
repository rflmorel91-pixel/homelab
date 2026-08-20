from fastapi import APIRouter


router = APIRouter(
    prefix="/status",
    tags=["RenewalDesk"],
)


@router.get("")
def renewaldesk_status():
    return {
        "product": "renewaldesk",
        "status": "available",
    }
