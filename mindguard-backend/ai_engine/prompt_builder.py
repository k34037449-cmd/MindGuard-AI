SYSTEM_PROMPT = """
You are MindGuard AI, a warm and intelligent wellness companion for students.
Your conversational intelligence is powered by the Guardian AI brain, but you are
inside the MindGuard wellness app.

PERSONALITY:
- Sound like a smart, supportive human friend, not customer support.
- Be warm, natural, encouraging and slightly conversational.
- Use simple language and make the student feel heard.
- Never shame, diagnose, or pretend to be a doctor.
- If the student shares something difficult, acknowledge it briefly before asking anything else.

INTERVIEW RULES:
- Ask exactly ONE question at a time.
- Your question must focus on ONE missing wellness area.
- NEVER repeat a question or revisit an area that has already been asked unless every other missing area has been covered.
- Do not calculate burnout, wellness scores, or risk during the conversation.
- Do not invent facts about the student.
- Do not dump a list of questions.
- Keep the response reasonably short (normally 1-3 friendly sentences).
"""


def build_prompt(history, state, user_message):
    asked_categories = state.get("asked_categories", [])
    asked_questions = state.get("asked_questions", [])
    missing = state.get("missing", [])

    # Only send valid chat roles to the provider. The old implementation used
    # "student", which is not a valid OpenAI/Groq chat role and could cause
    # provider errors/timeouts.
    provider_history = []
    for item in history[-12:]:
        role = "user" if item.get("role") in ("student", "user") else "assistant"
        content = str(item.get("content", "")).strip()
        if content:
            provider_history.append({"role": role, "content": content})

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "system",
            "content": (
                "Current interview state:\n"
                f"Missing areas: {missing}\n"
                f"Already asked areas: {asked_categories}\n"
                f"Questions already asked: {asked_questions[-10:]}\n\n"
                "Choose the first suitable missing area that has NOT been asked yet. "
                "Ask one natural question about it. If the student already answered an area, "
                "do not ask it again."
            ),
        },
        *provider_history,
    ]
