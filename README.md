# NEUROFLOW AI

Premium AI YouTube Automation & Video Production SaaS Platform.

## Architecture
- **Frontend (`frontend/`)**: Vite, React, TypeScript, Tailwind CSS, TanStack Query, Zustand, Supabase Auth — deployed on **Vercel**.
- **Backend (`backend/`)**: FastAPI, SQLAlchemy, Pydantic, WebSockets, Fernet credential encryption — deployed on **Docker / Railway / Render / VPS**.
- **Media Workers (`docker/Dockerfile.worker`)**: Celery + Redis + FFmpeg + `faster-whisper` + headless Blender 3D rendering.
- **Database & Storage (`supabase/`)**: Supabase PostgreSQL with Row Level Security (RLS) and private Storage (`neuroflow-media`).

## Quick Start
1. Run `supabase/migrations/0001_initial_schema.sql` in Supabase SQL Editor and create private Storage bucket `neuroflow-media`.
2. Copy `.env.example` to `.env`, set `CREDENTIAL_ENCRYPTION_KEY`, Supabase, and Google OAuth credentials.
3. Run `docker compose up --build -d` for backend + Redis + Celery workers.
4. Run `cd frontend && npm install && npm run dev` for the Vite UI.
