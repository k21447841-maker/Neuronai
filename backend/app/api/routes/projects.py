from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_current_user_id
from app.database.session import get_db
from app.models.models import Project
from app.schemas.schemas import ProjectCreate

router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.get("")
def list_projects(user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    rows = db.query(Project).filter(Project.user_id == user_id).order_by(Project.created_at.desc()).all()
    return [
        {
            "id": str(r.id), "title": r.title, "topic": r.topic, "niche": r.niche,
            "format": r.format, "aspect_ratio": r.aspect_ratio,
            "target_duration_seconds": r.target_duration_seconds,
            "language": r.language, "status": r.status, "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.post("")
def create_project(body: ProjectCreate, user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    p = Project(
        user_id=user_id, title=body.title, topic=body.topic, niche=body.niche, format=body.format,
        aspect_ratio=body.aspect_ratio, target_duration_seconds=body.target_duration_seconds, language=body.language,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"id": str(p.id), "title": p.title, "status": p.status}


@router.delete("/{project_id}")
def delete_project(project_id: UUID, user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    p = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(p)
    db.commit()
    return {"deleted": True}
