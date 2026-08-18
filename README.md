# Datamart LangChain Agent

A custom-coded Agentic AI chatbot for Datamart built with **LangChain**, **FastAPI**, **React**, **SQLite**, and **Chroma**. No n8n is used.

## Phase plan

- **Phase 1:** LangChain agent, custom tools, RAG, SQLite persistence, memory, FastAPI API
- **Phase 2:** React chat UI, document upload/management, richer lead/meeting flows
- **Phase 3:** Google Calendar + email notifications + human handoff dashboard
- **Phase 4:** Production hardening, LangSmith tracing/evals, deployment

## Current agent capabilities

- Answers Datamart knowledge questions through a RAG tool
- Captures project/lead information through a custom LangChain tool
- Saves meeting requests through a custom LangChain tool
- Saves human handoff requests
- Remembers recent conversation history per `conversation_id`

## Backend quick start

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
# add GROQ_API_KEY
python -m app.rag.ingest
uvicorn app.main:app --reload --port 8000
```

Open Swagger at `http://localhost:8000/docs`.

## Ingest company knowledge

Place `.txt`, `.md`, `.pdf`, or `.docx` files in `backend/knowledge/`, then run:

```bash
python -m app.rag.ingest
```

## Chat API

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What services does Datamart provide?"}'
```
