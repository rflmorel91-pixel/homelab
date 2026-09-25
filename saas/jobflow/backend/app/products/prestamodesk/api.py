from fastapi import APIRouter


router = APIRouter(
    tags=["PréstamoDesk"],
)


@router.get("/status")
def prestamodesk_status() -> dict[str, str]:
    return {
        "product": "prestamodesk",
        "name": "PréstamoDesk",
        "version": "0.1.0",
        "status": "available",
        "market": "Dominican Republic",
        "currency": "DOP",
        "language": "es",
    }
