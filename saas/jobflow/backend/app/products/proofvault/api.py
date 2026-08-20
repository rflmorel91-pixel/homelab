from fastapi import APIRouter


router = APIRouter(
    prefix="/status",
    tags=["ProofVault"],
)


@router.get("")
def proofvault_status():
    return {
        "product": "proofvault",
        "status": "available",
    }
