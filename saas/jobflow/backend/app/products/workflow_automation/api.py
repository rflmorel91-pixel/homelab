from fastapi import APIRouter


router = APIRouter(
    tags=["Workflow Automation Package"],
)


@router.get("/status")
def workflow_automation_status():
    return {
        "product": "workflow-automation",
        "name": "Workflow Automation Package",
        "offering_type": "service",
        "status": "available",
    }
