import uuid
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.deps import get_current_user_id
from app.database.session import get_db
from app.models.models import AutomationRun, AutomationWorkflow
from app.schemas.schemas import AutomationWorkflowCreate
from app.workers.automation_runner import run_automation_pipeline

router = APIRouter(prefix="/api/automation", tags=["Automation"])


@router.get("/workflows")
def list_workflows(user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return [
        {"id": str(w.id), "name": w.name, "niche": w.niche, "video_format": w.video_format, "schedule_cron": w.schedule_cron, "approval_mode": w.approval_mode, "status": w.status, "last_run_at": w.last_run_at.isoformat() if w.last_run_at else None}
        for w in db.query(AutomationWorkflow).filter(AutomationWorkflow.user_id == user_id).order_by(AutomationWorkflow.created_at.desc()).all()
    ]


@router.post("/workflows")
def create_workflow(body: AutomationWorkflowCreate, user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    wf = AutomationWorkflow(user_id=user_id, **body.model_dump())
    db.add(wf)
    db.commit()
    db.refresh(wf)
    return {"id": str(wf.id), "status": wf.status}


@router.patch("/workflows/{workflow_id}/status")
def set_workflow_status(workflow_id: UUID, status: str, user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    if status not in ("active", "paused", "stopped"):
        raise HTTPException(status_code=400, detail="Invalid workflow status")
    wf = db.query(AutomationWorkflow).filter(AutomationWorkflow.id == workflow_id, AutomationWorkflow.user_id == user_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    wf.status = status
    db.commit()
    return {"id": str(wf.id), "status": wf.status}


@router.post("/workflows/{workflow_id}/run")
def trigger_workflow(workflow_id: UUID, topic: str = Query(..., min_length=3), user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    wf = db.query(AutomationWorkflow).filter(AutomationWorkflow.id == workflow_id, AutomationWorkflow.user_id == user_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    idem_key = f"manual:{workflow_id}:{uuid.uuid4()}"
    run_automation_pipeline.delay(str(wf.id), topic, idem_key)
    return {"queued": True, "idempotency_key": idem_key}


@router.get("/runs")
def list_runs(user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return [
        {"id": str(r.id), "workflow_id": str(r.workflow_id), "current_step": r.current_step, "status": r.status, "error_message": r.error_message, "started_at": r.started_at.isoformat()}
        for r in db.query(AutomationRun).filter(AutomationRun.user_id == user_id).order_by(AutomationRun.started_at.desc()).limit(25).all()
    ]
