# NEUROFLOW AI — Production Deployment Guide

1. **Supabase**: Run `supabase/migrations/0001_initial_schema.sql`, create private bucket `neuroflow-media`, enable Email & Google Auth.
2. **Backend & Workers**: Deploy `docker/Dockerfile.backend` and `docker/Dockerfile.worker` with Managed Redis on Railway, Render, Fly.io, or a GPU VPS.
3. **Vercel Frontend**: Import GitHub repo on Vercel -> Set Root Directory to `frontend` -> Set `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_BASE_URL` -> Deploy.
