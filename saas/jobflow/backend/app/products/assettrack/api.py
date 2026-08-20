from fastapi import APIRouter


router = APIRouter(
    prefix="/status",
    tags=["AssetTrack"],
)


@router.get("")
def assettrack_status():
    return {
        "product": "assettrack",
        "status": "available",
    }
