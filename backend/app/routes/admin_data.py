from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models import HandoffRequest, Lead, MeetingRequest
from app.db.session import get_db


router = APIRouter(prefix="/api", tags=["data"])


@router.get("/leads")
def list_leads(db: Session = Depends(get_db)):
    rows = db.query(Lead).order_by(Lead.id.desc()).all()
    return [
        {
            "id": row.id,
            "conversation_id": row.conversation_id,
            "name": row.name,
            "email": row.email,
            "phone": row.phone,
            "company": row.company,
            "project_description": row.project_description,
            "budget": row.budget,
            "timeline": row.timeline,
            "status": row.status,
        }
        for row in rows
    ]


@router.get("/meetings")
def list_meetings(db: Session = Depends(get_db)):
    rows = db.query(MeetingRequest).order_by(MeetingRequest.id.desc()).all()
    return [
        {
            "id": row.id,
            "conversation_id": row.conversation_id,
            "name": row.name,
            "email": row.email,
            "preferred_date": row.preferred_date,
            "preferred_time": row.preferred_time,
            "timezone": row.timezone,
            "notes": row.notes,
            "status": row.status,
        }
        for row in rows
    ]


@router.get("/handoffs")
def list_handoffs(db: Session = Depends(get_db)):
    rows = db.query(HandoffRequest).order_by(HandoffRequest.id.desc()).all()
    return [
        {
            "id": row.id,
            "conversation_id": row.conversation_id,
            "reason": row.reason,
            "status": row.status,
        }
        for row in rows
    ]
