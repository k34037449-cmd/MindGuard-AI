# MindGuard AI — Guardian Brain Merge

This package keeps the **MindGuard website** as the main product and keeps its existing:

- Login / registration / authentication
- Dashboard
- Wellness/progress views and progress bars
- Planner
- Settings
- Wellness report and burnout scoring engine

The Guardian AI brain has been merged into the MindGuard backend as the conversational layer.

## What was fixed

1. **Repeated-question protection**
   - The interview now remembers categories and questions already asked.
   - The AI is explicitly told not to repeat a covered area.
   - A duplicate-response detector catches near-identical AI questions and replaces them with a fresh question.

2. **AI timeout protection**
   - Groq requests now use a bounded timeout and one short retry.
   - If Groq is temporarily unavailable, MindGuard falls back to a deterministic friendly question instead of hanging or crashing.

3. **Guardian-style conversation**
   - The MindGuard AI now uses Guardian's warm, natural, human-like conversational style while remaining a wellness interviewer.
   - The website branding remains **MindGuard AI**.

4. **Provider-role bug fixed**
   - The old MindGuard conversation history used `student` as an LLM role. It is now translated to the valid `user` role before sending the conversation to Groq.

## Run locally on Windows

### 1. Backend

Open Command Prompt in `mindguard-backend`:

```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Backend runs at `http://localhost:5000`.

### 2. Frontend

Open another Command Prompt in `mindguard-frontend`:

```bat
npm install
npm run dev
```

Open the Vite URL shown in the terminal.

The frontend's Vite proxy sends `/api` requests to `http://localhost:5000`.

## API key

The merged backend contains the Groq configuration from the supplied Guardian project in `mindguard-backend/.env`.

Do not commit `.env` to GitHub. If this project will be shared publicly, rotate the Groq key and replace it with a new one.

## Pre-run debug verification (Oct 27, 2026)

The backend AI logic was statically compiled and targeted with regression tests before packaging.

Fixes verified:
- Assistant questions are no longer treated as student answers/facts.
- Asked interview categories persist across requests using conversation history metadata.
- Duplicate/near-duplicate AI questions are blocked with a deterministic category-matched fallback.
- The fallback no longer skips the category that triggered the duplicate.
- Invalid `student` provider role is normalized to `user`.
- Groq request timeout/retry/fallback protection remains enabled.
- Frontend source and API wiring were inspected; dependency installation/build should be run on Windows with `npm install`.

Note: a full Flask runtime smoke test could not be executed in this sandbox because Flask is not installed here, and a frontend `npm ci` exceeded the sandbox network/time limit. The Python modules themselves pass `py_compile`, and the AI regression tests pass.

## Normal AI Chat + Wellness Check

The `/app/chat` screen now has two separate modes:
- **Normal AI Chat** — general Guardian/Groq-style assistant for study help, timetables, planning, explanations and ordinary conversation.
- **Wellness Check** — the original MindGuard wellness interview, including its duplicate-question protection, state tracking, report generation and progress integration.

The normal chat uses `/api/chat` and does not call the wellness interview engine. The wellness mode continues to use `/api/interview` unchanged.
