# MindGuard test status (2026-10-30)

## Verified in this workspace

- Python source files compile with `python -m compileall`.
- Offline normal-chat fallback tests pass for arithmetic (`2 + 2`), greeting, motivation, photosynthesis, and MindGuard-vs-ChatGPT comparison.
- Offline timetable fallback tests pass for a three-hour duration and an explicit 6 PM–10 PM window.
- Timetable fallback now treats a requested duration as focused study time and adds breaks outside that duration.
- Progress charts use saved assessment records returned by the authenticated API. The page shows an empty state when there are no records and a separate error state when the API cannot be reached. The misleading chart labelled “Planner Completion” was removed; it had plotted wellness scores, not planner completion.
- No live `.env`, database, Python cache, or `node_modules` directory is included in this ZIP.

## Not verified here — do not claim otherwise

- Live Groq responses: requires a valid, newly rotated `GROQ_API_KEY` configured in the backend environment.
- Full Flask runtime/API tests: Flask dependencies are not installed in this workspace.
- Frontend production build: `npm ci` did not finish within the available test window, so `npm run build` has not been verified.
- Browser end-to-end tests, GitHub push, and Render deployment have not been performed.

## Run the included fallback tests

From `mindguard-backend`:

```bash
python -m unittest discover -s tests -v
```

A working Groq connection is required for broad open-ended questions such as “Explain Newton's laws”. The offline fallback deliberately reports provider unavailability rather than inventing a generic explanation.
