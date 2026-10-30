import os
import re
import time
import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "llama-3.3-70b-versatile"

FALLBACK_QUESTIONS = {
    "academic_load": "How are your studies feeling right now — manageable, heavy, or overwhelming?",
    "sleep": "How has your sleep been lately, including roughly how many hours you get?",
    "stress": "How has your stress been lately, and what usually makes it worse?",
    "motivation": "How has your motivation to study or get things done been recently?",
    "mood": "How has your mood been over the last few days?",
    "cognitive": "How have your concentration, focus, and memory been lately?",
    "lifestyle": "How would you describe your everyday routine, meals, and general self-care?",
    "time_management": "How are you managing your time between studies, rest, and other things?",
    "social_support": "When things get difficult, do you have someone you feel comfortable talking to?",
    "digital_behaviour": "How has your phone or screen time been affecting your routine, if at all?",
    "recent_life_events": "Has anything important or stressful changed in your life recently?",
    "emotional_exhaustion": "Have you been feeling emotionally drained lately, or are you generally able to recharge?",
    "burnout_symptoms": "Have you recently felt overwhelmed, detached, or like you are running out of energy?",
    "anxiety": "Have you been worrying or feeling nervous more than usual lately?",
    "productivity": "How have you been doing with actually finishing the things you need to get done?",
    "exercise": "How much physical activity or movement are you getting in a typical week?",
}


def fallback_for_state(state):
    missing = (state or {}).get("missing") or []
    asked = set((state or {}).get("asked_categories") or [])
    for category in missing:
        if category not in asked:
            return FALLBACK_QUESTIONS.get(category, "Tell me a little more about how things have been going for you lately.")
    for category in missing:
        return FALLBACK_QUESTIONS.get(category, "Tell me a little more about how things have been going for you lately.")
    return "Thanks for opening up. I have enough information to put your wellness picture together."


def _extract_reply(data):
    try:
        reply = data["choices"][0]["message"]["content"].strip()
        if not reply:
            raise ValueError("Empty LLM response")
        return reply
    except (KeyError, IndexError, TypeError, AttributeError):
        raise ValueError("Invalid LLM response format")


def _provider_settings():
    provider = os.getenv("LLM_PROVIDER", "groq").lower()
    api_key = os.getenv(f"{provider.upper()}_API_KEY")
    if provider == "openrouter":
        api_url = os.getenv("OPENROUTER_URL", DEFAULT_OPENROUTER_URL)
        model = os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL)
    else:
        api_url = os.getenv("GROQ_URL", DEFAULT_GROQ_URL)
        model = os.getenv("GROQ_MODEL", DEFAULT_MODEL)
    return provider, api_key, api_url, model


def _call_provider(messages, temperature, max_tokens):
    _provider, api_key, api_url, model = _provider_settings()
    if not api_key:
        return None

    try:
        timeout = max(3.0, float(os.getenv("GROQ_TIMEOUT", "18")))
    except ValueError:
        timeout = 18.0
    try:
        retries = max(0, int(os.getenv("GROQ_RETRIES", "1")))
    except ValueError:
        retries = 1

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    last_error = None
    for attempt in range(retries + 1):
        try:
            response = requests.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=(5, timeout),
            )
            response.raise_for_status()
            return _extract_reply(response.json())
        except (requests.RequestException, ValueError) as error:
            last_error = error
            if attempt < retries:
                time.sleep(0.35)

    print(f"[MindGuard AI] Provider unavailable: {last_error}")
    return None


def ask_llm(messages, state=None):
    """Guardian/Groq brain for the protected wellness interview.

    This path intentionally keeps the wellness fallback separate from normal chat.
    """
    reply = _call_provider(messages, temperature=0.55, max_tokens=350)
    return reply if reply else fallback_for_state(state)


def _last_user_message(messages):
    for item in reversed(messages or []):
        if isinstance(item, dict) and item.get("role") == "user":
            return str(item.get("content", "")).strip()
    return ""


def _contains_any(text, phrases):
    return any(phrase in text for phrase in phrases)


def _number_from_text(text, default=3):
    match = re.search(r"\b(\d+)\s*(?:-?hour|hours|hr)\b", text)
    if match:
        return max(1, min(12, int(match.group(1))))
    return default


def _fallback_timetable(user_text):
    hours = _number_from_text(user_text, 3)
    start = 18 * 60
    block = 45
    short_break = 10
    lines = ["Absolutely bro 💪 Here’s a realistic study plan you can start right now:"]
    for index in range(hours):
        start_min = start + index * (block + short_break)
        end_min = start_min + block
        sh, sm = divmod(start_min, 60)
        eh, em = divmod(end_min, 60)
        task = [
            "Core concepts / weakest topic",
            "Practice questions and examples",
            "Revision + active recall",
            "Past-paper questions",
            "Difficult problems / mistakes",
            "Quick final revision",
        ][index % 6]
        lines.append(f"{sh:02d}:{sm:02d}–{eh:02d}:{em:02d} — {task}")
        if index < hours - 1:
            bstart = end_min
            bend = bstart + short_break
            bh, bm = divmod(bstart, 60)
            eh2, em2 = divmod(bend, 60)
            lines.append(f"{bh:02d}:{bm:02d}–{eh2:02d}:{em2:02d} — Short break: walk around, drink water, no guilt.")
    lines.append("\nStart with just the first block. You don't need to feel motivated before you begin — starting is what creates the momentum.")
    return "\n".join(lines)


def _general_chat_fallback(messages):
    """Useful offline fallback for normal chat.

    It must answer the request instead of asking the student to repeat information.
    This is only used when the configured LLM provider is unavailable.
    """
    user_text = _last_user_message(messages)
    lower = user_text.lower()

    if _contains_any(lower, ("timetable", "time table", "study plan", "schedule")):
        return _fallback_timetable(user_text)

    # Handle simple arithmetic locally when the language-model provider is
    # unavailable. Never evaluate arbitrary Python supplied by a user.
    arithmetic = re.fullmatch(r"\s*(?:what is\s+)?(-?\d+(?:\.\d+)?)\s*([+\-*/x])\s*(-?\d+(?:\.\d+)?)\s*\??\s*", lower)
    if arithmetic:
        left, operator, right = arithmetic.groups()
        a, b = float(left), float(right)
        if operator in ("+",):
            result = a + b
        elif operator == "-":
            result = a - b
        elif operator in ("*", "x"):
            result = a * b
        elif operator == "/" and b != 0:
            result = a / b
        else:
            return "I can't divide by zero. Try a non-zero divisor."
        shown = int(result) if result.is_integer() else result
        return f"{left} {operator} {right} = {shown}.\n\nI worked that out directly; ask me if you'd like the steps too."

    if "difference between" in lower and "chatgpt" in lower:
        return (
            "MindGuard is designed around student support: it combines general AI chat, "
            "study planning and a separate wellness check-in. ChatGPT is a general-purpose "
            "assistant for a much wider range of tasks. MindGuard's goal is a focused student "
            "experience; its answer quality still depends on the AI model configured by the developer."
        )

    # A small, verified offline explanation for a common presentation/demo topic.
    # Open-ended explanations still use Groq; when it is offline we say so rather
    # than pretending a generic placeholder is a real answer.
    if "photosynthesis" in lower:
        return (
            "Photosynthesis is the process by which green plants make their own food using light energy.\n\n"
            "1. Roots absorb water from the soil.\n"
            "2. Leaves take in carbon dioxide through tiny openings called stomata.\n"
            "3. Chlorophyll in chloroplasts absorbs sunlight.\n"
            "4. Light energy helps convert water and carbon dioxide into glucose; oxygen is released.\n\n"
            "Word equation: carbon dioxide + water + light energy → glucose + oxygen.\n"
            "In short, photosynthesis stores light energy as chemical energy in glucose."
        )

    if lower.startswith(("explain ", "what is ", "define ")):
        return (
            "I can't give a reliable explanation while the AI model is disconnected. "
            "Please check that GROQ_API_KEY and GROQ_MODEL are configured on the backend, "
            "then retry. I don't want to make up an answer."
        )

    if _contains_any(lower, ("motivat", "procrastinat", "can't start", "cannot start", "give up", "demotiv")):
        return (
            "Hey bro ❤️ breathe for a second. You don't need to fix your whole life tonight. "
            "Do one small thing for the next 15 minutes: put your phone away, open the easiest "
            "topic, and solve just 2 questions. Once you start, momentum usually becomes easier.\n\n"
            "For the next hour: 25 min focused study → 5 min break → 25 min focused study → 5 min break. "
            "Your only job is to begin."
        )

    if _contains_any(lower, ("integration of cot", "integral of cot", "∫ cot", "integrate cot")):
        return (
            "Sure bro — let's do it step by step.\n\n"
            "∫ cot x dx\n"
            "= ∫ (cos x / sin x) dx\n\n"
            "Let u = sin x, so du = cos x dx.\n"
            "Therefore:\n"
            "∫ du/u = ln|u| + C\n\n"
            "Substitute back u = sin x:\n"
            "∫ cot x dx = ln|sin x| + C.\n\n"
            "Quick memory trick: cot x = cos x/sin x, so the answer is ln|sin x| + C."
        )

    if _contains_any(lower, ("exam", "revision", "study", "maths", "mathematics", "physics", "chemistry")):
        return (
            "You've got this bro 💪 Don't try to finish everything at once. Pick the highest-priority topic, "
            "study it for 25 minutes, then do 5 minutes of active recall. Repeat that cycle twice, then take "
            "a proper short break. If you have a few hours, keep the final block for questions rather than "
            "only rereading notes."
        )

    if _contains_any(lower, ("hello", "hi", "hey", "bro")):
        return "Hey bro 👋 I'm here. Ask me anything — study help, explanations, timetables, planning, or just talk to me."

    return (
        "I received your message, but my AI model is not connected right now. "
        "Please check the GROQ_API_KEY and GROQ_MODEL environment variables on the backend, "
        "then restart the service. I won't pretend I generated an AI answer when the provider is offline."
    )


def ask_general_llm(messages):
    """Guardian/Groq-backed normal chat with a strong, useful local fallback."""
    reply = _call_provider(messages, temperature=0.65, max_tokens=700)
    return reply if reply else _general_chat_fallback(messages)
