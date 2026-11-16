import json
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_current_user_id, get_decrypted_provider_credential
from app.database.session import get_db
from app.models.models import Project, Scene, Script, ScriptVersion, UsageLog
from app.providers.llm_adapters import get_llm_provider
from app.schemas.schemas import ScriptEditSectionRequest, ScriptGenerateRequest

router = APIRouter(prefix="/api/scripts", tags=["Scripts & Scenes"])


@router.get("/project/{project_id}")
def get_project_script_and_scenes(project_id: UUID, user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    script = db.query(Script).filter(Script.project_id == project_id, Script.user_id == user_id).order_by(Script.created_at.desc()).first()
    scenes = db.query(Scene).filter(Scene.project_id == project_id, Scene.user_id == user_id).order_by(Scene.scene_number).all()
    versions = db.query(ScriptVersion).filter(ScriptVersion.script_id == script.id).order_by(ScriptVersion.version_number.desc()).all() if script else []
    return {
        "script": {
            "id": str(script.id), "hook": script.hook, "introduction": script.introduction,
            "body": script.body, "ending": script.ending, "call_to_action": script.call_to_action,
            "full_text": script.full_text, "current_version": script.current_version,
            "provider_slug": script.provider_slug, "model_used": script.model_used,
        } if script else None,
        "versions": [{"version_number": v.version_number, "change_note": v.change_note, "created_at": v.created_at.isoformat()} for v in versions],
        "scenes": [
            {
                "id": str(s.id), "scene_number": s.scene_number, "narration": s.narration,
                "estimated_duration_seconds": float(s.estimated_duration_seconds),
                "visual_description": s.visual_description, "camera_movement": s.camera_movement,
                "character_description": s.character_description, "background_description": s.background_description,
                "sound_effects_cue": s.sound_effects_cue, "subtitle_text": s.subtitle_text, "animation_mode": s.animation_mode,
            }
            for s in scenes
        ],
    }


@router.post("/generate")
async def generate_script(body: ScriptGenerateRequest, user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == body.project_id, Project.user_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    cred, api_key = get_decrypted_provider_credential(db, user_id, body.provider_slug)
    resp = await get_llm_provider(body.provider_slug).generate_text(
        api_key=api_key, model=cred.selected_model,
        system_prompt="Return valid JSON ONLY with keys: hook, introduction, body, ending, call_to_action, scenes (array of scene_number, narration, estimated_duration_seconds, visual_description, camera_movement, character_description, background_description, sound_effects_cue, subtitle_text).",
        user_prompt=f"Topic: {body.topic}\nNiche: {body.niche}\nLanguage: {body.language}\nAudience: {body.target_audience}\nFormat: {body.content_format}\nDuration: {body.duration_seconds}s\nTone: {body.tone}\nStyle: {body.storytelling_style}",
        temperature=body.creativity, timeout=cred.timeout_seconds,
    )
    cleaned = resp.content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"Provider returned non-JSON script: {exc}") from exc

    full_text = "\n\n".join(filter(None, [parsed.get("hook", ""), parsed.get("introduction", ""), parsed.get("body", ""), parsed.get("ending", ""), parsed.get("call_to_action", "")]))
    script = Script(
        user_id=user_id, project_id=project.id, provider_slug=body.provider_slug, model_used=resp.model,
        tone=body.tone, storytelling_style=body.storytelling_style, hook=parsed.get("hook", ""),
        introduction=parsed.get("introduction", ""), body=parsed.get("body", ""),
        ending=parsed.get("ending", ""), call_to_action=parsed.get("call_to_action", ""),
        full_text=full_text, current_version=1,
    )
    db.add(script)
    db.flush()
    db.add(ScriptVersion(user_id=user_id, script_id=script.id, version_number=1, content_snapshot=parsed, change_note="Initial AI generation"))
    db.query(Scene).filter(Scene.project_id == project.id).delete()
    for idx, sc in enumerate(parsed.get("scenes", []), start=1):
        db.add(Scene(
            user_id=user_id, project_id=project.id, script_id=script.id, scene_number=sc.get("scene_number", idx),
            narration=sc.get("narration", ""), estimated_duration_seconds=sc.get("estimated_duration_seconds", 5.0),
            visual_description=sc.get("visual_description", ""), camera_movement=sc.get("camera_movement", "slow_zoom_in"),
            character_description=sc.get("character_description", ""), background_description=sc.get("background_description", ""),
            sound_effects_cue=sc.get("sound_effects_cue", ""), subtitle_text=sc.get("subtitle_text", sc.get("narration", "")),
        ))
    db.add(UsageLog(user_id=user_id, provider_slug=body.provider_slug, operation="script_generation", units_consumed=resp.input_tokens + resp.output_tokens, unit_type="tokens", metadata_json={"model": resp.model}))
    project.status = "scripting"
    db.commit()
    return {"script_id": str(script.id), "scene_count": len(parsed.get("scenes", []))}


@router.post("/edit-section")
async def edit_script_section(body: ScriptEditSectionRequest, user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    if not db.query(Script).filter(Script.id == body.script_id, Script.user_id == user_id).first():
        raise HTTPException(status_code=404, detail="Script not found")
    cred, api_key = get_decrypted_provider_credential(db, user_id, body.provider_slug)
    instr = f"Perform '{body.action}' on this script excerpt."
    if body.target_tone:
        instr += f" Tone: {body.target_tone}."
    if body.target_language:
        instr += f" Language: {body.target_language}."
    resp = await get_llm_provider(body.provider_slug).generate_text(api_key, cred.selected_model, "Return only revised text.", f"{instr}\n\n{body.selected_text}", timeout=cred.timeout_seconds)
    return {"revised_text": resp.content.strip()}
