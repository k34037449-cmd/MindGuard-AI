# MindGuard — fast GitHub + Render deployment

## Before uploading
1. **Rotate the Groq API key immediately.** The uploaded archive contained a live-looking key in `mindguard-backend/.env`. Treat it as compromised: revoke it in the Groq console and create a new one. Do not commit `.env`.
2. This cleaned package excludes virtual environments, `node_modules`, caches, databases and `.env` secrets.
3. The Vite base path is `/` for a Render root-domain deployment.

## GitHub
Create an empty GitHub repository. In a terminal, from this folder:
```bash
git init
git add .
git commit -m "Prepare MindGuard for presentation deployment"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

## Render backend
Create **New + → Web Service**, connect the GitHub repository:
- Root Directory: `mindguard-backend`
- Runtime: Python
- Build Command: `pip install -r requirements.txt`
- Start Command: `waitress-serve --listen=0.0.0.0:$PORT app:app`

Add environment variables:
- `LLM_PROVIDER` = `groq`
- `GROQ_API_KEY` = your newly generated key (never put it in GitHub)
- `GROQ_MODEL` = `llama-3.3-70b-versatile`
- `SECRET_KEY` = a long random secret
- `PYTHON_VERSION` = `3.11.9`

After deploy, open `https://YOUR-BACKEND.onrender.com/` and confirm it returns JSON with status `running`.

## Render frontend
Create **New + → Static Site**, same repository:
- Root Directory: `mindguard-frontend`
- Build Command: `npm install && npm run build`
- Publish Directory: `dist`
- Environment variable: `VITE_API_URL` = `https://YOUR-BACKEND.onrender.com/api`

Redeploy the frontend after setting the API URL. Replace the placeholder with your real backend URL.

## Important demo/data honesty
- Normal AI Chat and Wellness Check are separate modes. The normal chat depends on the configured Groq model.
- The Progress page builds charts from saved assessment records returned by `/api/progress`. With no saved assessments it should show “No assessment history yet”, not fabricated chart points.
- Do not present sample/mock profile values as real student measurements. Use a test account and complete a real check-in before showing a personal trend.
- Render's local SQLite database may not be durable across service restarts/redeploys on a free instance. For a real multi-user launch, migrate to managed PostgreSQL and configure persistent storage. For tomorrow's demo, disclose this limitation.

## Quick smoke tests
- Backend `/` returns `{"status":"running","project":"MindGuard AI"}`.
- Login/register works and `/api/chat` returns an actual model response.
- Try `2 + 2`, “Explain photosynthesis”, “Motivate me”, and a timetable request.
- Complete a wellness check; then refresh Progress and confirm it plots only saved assessments.
