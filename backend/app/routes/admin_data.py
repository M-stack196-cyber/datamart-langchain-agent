from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Literal

from app.auth import require_admin
from app.db.models import HandoffRequest, Lead, MeetingRequest
from app.db.session import get_db


router = APIRouter(
    prefix="/api",
    tags=["admin-data"],
    dependencies=[Depends(require_admin)],
)


@router.get("/leads")
def list_leads(
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Lead)
        .order_by(Lead.id.desc())
        .all()
    )

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


class LeadStatusUpdate(BaseModel):
    status: Literal[
        "new",
        "contacted",
        "qualified",
        "converted",
        "lost",
    ]


@router.patch("/leads/{lead_id}/status")
def update_lead_status(
    lead_id: int,
    payload: LeadStatusUpdate,
    db: Session = Depends(get_db),
):
    lead = (
        db.query(Lead)
        .filter(Lead.id == lead_id)
        .first()
    )

    if not lead:
        raise HTTPException(
            status_code=404,
            detail="Lead not found",
        )

    lead.status = payload.status
    db.commit()
    db.refresh(lead)

    return {
        "id": lead.id,
        "status": lead.status,
        "message": "Lead status updated successfully.",
    }


@router.get("/meetings")
def list_meetings(
    db: Session = Depends(get_db),
):
    rows = (
        db.query(MeetingRequest)
        .order_by(MeetingRequest.id.desc())
        .all()
    )

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
def list_handoffs(
    db: Session = Depends(get_db),
):
    rows = (
        db.query(HandoffRequest)
        .order_by(HandoffRequest.id.desc())
        .all()
    )

    return [
        {
            "id": row.id,
            "conversation_id": row.conversation_id,
            "reason": row.reason,
            "status": row.status,
        }
        for row in rows
    ]