# MindGuard AI

MindGuard combines student-focused general AI chat, study planning, a separate wellness check-in, and progress tracking based on saved assessments.

## Project structure

- `mindguard-backend/` — Flask API, AI connector, wellness assessment engine, database models.
- `mindguard-frontend/` — React + Vite web application.

## Run locally

Backend (Python 3.11 recommended):

```bash
cd mindguard-backend
python -m venv venv
# Windows: venv\\Scripts\\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env  # Windows; on macOS/Linux use: cp .env.example .env
python app.py
```

Set a valid `GROQ_API_KEY` in the backend `.env` for open-ended AI answers. Never commit `.env`.

Frontend (second terminal):

```bash
cd mindguard-frontend
npm install
npm run dev
```

## Tests

From `mindguard-backend` run:

```bash
python -m unittest discover -s tests -v
```

See `TEST_RESULTS.md` for what has and has not been verified. See `DEPLOY_TONIGHT.md` for Render deployment steps.
