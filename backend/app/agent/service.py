import re
from typing import Optional

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_groq import ChatGroq
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import HandoffRequest, Lead, MeetingRequest
from app.agent.prompts import SYSTEM_PROMPT
from app.rag.vectorstore import get_retriever


EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def build_datamart_agent(db: Session, conversation_id: str):
    settings = get_settings()

    @tool
    def search_datamart_knowledge(query: str) -> str:
        """
        Search the verified Datamart knowledge base.

        Use this tool for Datamart-specific information such as:
        services, capabilities, company information, solutions,
        policies, technologies, and other verified company facts.
        """

        try:
            documents = get_retriever(k=4).invoke(query)
        except Exception as exc:
            return f"Knowledge search failed: {exc}"

        if not documents:
            return "No verified Datamart knowledge was found for this question."

        parts = []

        for index, document in enumerate(documents, start=1):
            source = (
                document.metadata.get("source_file")
                or document.metadata.get("source")
                or "unknown"
            )

            parts.append(
                f"[{index}] Source: {source}\n"
                f"{document.page_content}"
            )

        return "\n\n".join(parts)

    @tool
    def save_lead_details(
        project_description: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        company: Optional[str] = None,
        budget: Optional[str] = None,
        timeline: Optional[str] = None,
    ) -> str:
        """
        Create or update a project lead from details explicitly
        provided by the visitor.

        Use this tool when the visitor is interested in Datamart
        services or has a genuine project enquiry.
        """

        lead = (
            db.query(Lead)
            .filter(Lead.conversation_id == conversation_id)
            .order_by(Lead.id.desc())
            .first()
        )

        if not lead:
            lead = Lead(conversation_id=conversation_id)
            db.add(lead)

        updates = {
            "name": name,
            "email": email,
            "phone": phone,
            "company": company,
            "project_description": project_description,
            "budget": budget,
            "timeline": timeline,
        }

        for field, value in updates.items():
            if value is not None and str(value).strip():
                setattr(
                    lead,
                    field,
                    str(value).strip(),
                )

        if lead.email and not EMAIL_RE.match(lead.email):
            lead.email = None

        db.commit()
        db.refresh(lead)

        missing = [
            field
            for field in ("name", "email")
            if not getattr(lead, field)
        ]

        if missing:
            return (
                "Lead saved. Still missing: "
                f"{', '.join(missing)}. "
                "Ask the visitor only for these missing fields."
            )

        return (
            f"Lead #{lead.id} saved successfully "
            "with name and email."
        )

    @tool
    def create_meeting_request(
        name: str,
        email: str,
        preferred_date: str,
        preferred_time: Optional[str] = None,
        timezone: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> str:
        """
        Save a meeting or call request.

        Use this after the visitor provides:
        name, email, and preferred date.

        This tool saves a request only.
        It does not confirm calendar availability.
        """

        email = email.strip().lower()

        if not EMAIL_RE.match(email):
            return (
                "The email address is invalid. "
                "Ask the visitor for a valid email before "
                "saving the meeting request."
            )

        meeting = MeetingRequest(
            conversation_id=conversation_id,
            name=name.strip(),
            email=email,
            preferred_date=preferred_date.strip(),
            preferred_time=(
                preferred_time.strip()
                if preferred_time
                else None
            ),
            timezone=(
                timezone.strip()
                if timezone
                else None
            ),
            notes=(
                notes.strip()
                if notes
                else None
            ),
        )

        db.add(meeting)
        db.commit()
        db.refresh(meeting)

        return (
            f"Meeting request #{meeting.id} saved. "
            "It is pending Datamart team confirmation. "
            "Do not tell the visitor that the slot is confirmed."
        )

    @tool
    def request_human_handoff(reason: str) -> str:
        """
        Create a human support handoff.

        Use this when the visitor explicitly asks to speak
        with a real person or requires human assistance.
        """

        handoff = HandoffRequest(
            conversation_id=conversation_id,
            reason=reason.strip(),
        )

        db.add(handoff)
        db.commit()
        db.refresh(handoff)

        return (
            f"Human handoff request #{handoff.id} "
            "created successfully."
        )

    if not settings.groq_api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured in the backend .env file."
        )

    model = ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=0,
        timeout=45,
        max_retries=2,
    )

    agent = create_agent(
        model=model,
        tools=[
            search_datamart_knowledge,
            save_lead_details,
            create_meeting_request,
            request_human_handoff,
        ],
        system_prompt=SYSTEM_PROMPT,
    )

    return agent