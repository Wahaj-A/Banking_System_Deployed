# Vercel deployment

This project is prepared as a single Vercel deployment:
- React/Vite frontend builds from `Frontend/` into `Frontend/dist`.
- FastAPI is exposed through `api/index.py`.
- FastAPI routes already include the `/api` prefix.
- `GEMINI_API_KEY` must be configured in Vercel Environment Variables.
- Do NOT upload `Backend/.env`.

Recommended Vercel settings:
- Root Directory: `./`
- Framework Preset: Other (or let Vercel auto-detect)
- Build Command: use the repository `vercel.json` value
- Output Directory: `Frontend/dist`

After adding `GEMINI_API_KEY`, redeploy the project.
