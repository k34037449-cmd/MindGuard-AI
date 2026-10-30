from difflib import SequenceMatcher
import re

from .llm_connector import ask_llm
from .prompt_builder import build_prompt
from .state_manager import create_state, update_state
from .extractor import extract_facts
from .completion_checker import is_complete


# HARD SAFETY NET:
# A question may NEVER be shown twice in one interview. We keep a generous
# history window so this still works even if the frontend/backend is refreshed.
MAX_REMEMBERED_QUESTIONS = 50
MAX_SIMILARITY = 0.74

EMERGENCY_QUESTIONS = {
    "academic_load": [
        "How manageable does your current schoolwork feel on most days?",
        "What part of your studies is taking the most energy from you right now?",
    ],
    "sleep": [
        "What has your sleep routine been like recently?",
        "When you wake up, do you usually feel rested or still tired?",
    ],
    "stress": [
        "What tends to put the most pressure on you these days?",
        "When you feel under pressure, how strongly does it affect you?",
    ],
    "motivation": [
        "How easy or difficult has it been to get yourself started on things lately?",
        "What usually helps you get moving when you do not feel motivated?",
    ],
    "mood": [
        "What has your general mood been like over the past few days?",
        "Have you been feeling mostly positive, neutral, or low recently?",
    ],
    "cognitive": [
        "How easy has it been to stay focused when you need to study?",
        "Have you noticed any changes in your memory or ability to concentrate?",
    ],
    "lifestyle": [
        "How balanced does your usual daily routine feel right now?",
        "How are you doing with meals, rest, and taking care of yourself?",
    ],
    "time_management": [
        "How well does your current schedule give you time for both work and rest?",
        "Where does your time tend to disappear on a typical day?",
    ],
    "social_support": [
        "When you need support, is there someone you can comfortably reach out to?",
        "How connected do you feel to the people around you at the moment?",
    ],
    "digital_behaviour": [
        "How much does your phone or screen use affect your day-to-day routine?",
        "Do you feel your screen habits are helping or getting in the way lately?",
    ],
    "recent_life_events": [
        "Has anything significant changed in your life recently?",
        "Is there a recent situation that has had a noticeable effect on you?",
    ],
    "emotional_exhaustion": [
        "After a busy day, how much emotional energy do you usually have left?",
        "Do you feel able to recharge after stressful or demanding days?",
    ],
    "burnout_symptoms": [
        "Have you recently felt like your usual energy or interest is running low?",
        "Do your responsibilities ever leave you feeling completely worn out?",
    ],
    "anxiety": [
        "How often have worries been getting in the way of your normal day?",
        "When something is uncertain, how difficult is it to switch your mind off?",
    ],
    "productivity": [
        "How satisfied are you with how much you are actually getting done?",
        "Are you generally able to finish the tasks you set out to do?",
    ],
    "exercise": [
        "How much movement or physical activity are you getting during a normal week?",
        "Do you get regular chances to move around or exercise during your day?",
    ],
}


def _normalize(text):
    text = re.sub(r"[^a-z0-9\s]", " ", (text or "").lower())
    return " ".join(text.split())


def _tokens(text):
    # Ignore tiny conversational words so similarity is based on the actual
    # meaning-bearing words in the question.
    return {w for w in _normalize(text).split() if len(w) > 2}


def _is_duplicate(reply, asked_questions):
    """Hard duplicate gate. True means the reply MUST NOT reach the user."""
    normalized = _normalize(reply)
    if not normalized:
        return True

    new_tokens = _tokens(normalized)
    for old in asked_questions[-MAX_REMEMBERED_QUESTIONS:]:
        old_normalized = _normalize(old)
        if not old_normalized:
            continue
        if normalized == old_normalized:
            return True
        if SequenceMatcher(None, normalized, old_normalized).ratio() >= MAX_SIMILARITY:
            return True
        old_tokens = _tokens(old_normalized)
        if new_tokens and old_tokens:
            overlap = len(new_tokens & old_tokens) / max(1, min(len(new_tokens), len(old_tokens)))
            if overlap >= 0.80:
                return True
    return False


def _looks_like_one_question(reply):
    """Reject model output that ignores the one-question interview contract."""
    text = (reply or "").strip()
    if not text:
        return False
    # Two or more question marks is a strong signal that the model asked a list.
    if text.count("?") > 1:
        return False
    # We only accept an interview reply containing an actual question.
    return "?" in text


def _pick_unasked_category(state):
    missing = state.get("missing", [])
    asked = set(state.get("asked_categories", []))
    for category in missing:
        if category not in asked:
            return category
    return None


def _emergency_unique_question(state, preferred_category=None):
    """Deterministic emergency path that guarantees we do not intentionally repeat."""
    asked_questions = state.get("asked_questions", [])
    asked_categories = set(state.get("asked_categories", []))
    missing = state.get("missing", [])

    ordered = []
    if preferred_category:
        ordered.append(preferred_category)
    ordered.extend(cat for cat in missing if cat not in ordered)

    for category in ordered:
        if category in asked_categories:
            continue
        for candidate in EMERGENCY_QUESTIONS.get(category, []):
            if not _is_duplicate(candidate, asked_questions):
                return candidate, category

    # State corruption guard: if the database says something is missing but all
    # known question templates have somehow been consumed, do NOT send a repeat.
    # Returning None tells the caller to end the interview safely.
    return None, None


def process_message(message, state=None):
    if state is None:
        state = create_state()

    state.setdefault("asked_categories", [])
    state.setdefault("asked_questions", [])
    state.setdefault("history", [])

    # Keep a bounded but sufficiently large server-side memory of questions.
    state["asked_questions"] = state["asked_questions"][-MAX_REMEMBERED_QUESTIONS:]

    # Store ONLY the student's message as a student turn.
    state["history"].append({"role": "student", "content": message})

    # Extract facts only from student messages. The AI must never answer its own
    # question and accidentally mark that wellness category as completed.
    student_text = "\n".join(
        item.get("content", "")
        for item in state["history"]
        if item.get("content") and item.get("role") in ("student", "user")
    )
    state = update_state(state, extract_facts(student_text))

    if is_complete(state):
        return {"complete": True, "data": state["data"], "state": state}

    target_category = _pick_unasked_category(state)
    if target_category is None:
        # Never manufacture another question when every remaining category has
        # already been asked. This is the ultimate stop condition.
        return {"complete": True, "data": state["data"], "state": state}

    prompt = build_prompt(state["history"], state, message)
    reply = ask_llm(prompt, state)

    # STRONG MEDICINE #1: reject duplicates.
    # STRONG MEDICINE #2: reject multi-question/model-garbage replies.
    if _is_duplicate(reply, state["asked_questions"]) or not _looks_like_one_question(reply):
        reply, target_category = _emergency_unique_question(state, target_category)

    # STRONG MEDICINE #3: if the emergency candidate is somehow duplicated too,
    # search every unasked category. Never send the unsafe provider output.
    if not reply or _is_duplicate(reply, state["asked_questions"]):
        reply, target_category = _emergency_unique_question(state)

    # STRONG MEDICINE #4: fail closed. It is better to finish than show a
    # repeated question to the student.
    if not reply:
        return {"complete": True, "data": state["data"], "state": state}

    if target_category and target_category not in state["asked_categories"]:
        state["asked_categories"].append(target_category)

    state["asked_questions"].append(reply)
    state["history"].append({
        "role": "assistant",
        "content": reply,
        "category": target_category,
    })

    # Re-run completion using student text only.
    if is_complete(state):
        return {"complete": True, "data": state["data"], "state": state}

    return {"complete": False, "reply": reply, "state": state}
