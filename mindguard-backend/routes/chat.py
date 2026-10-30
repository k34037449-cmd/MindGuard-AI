from flask import Blueprint, request, jsonify
from ai_engine.general_chat import generate_general_reply
from utils.auth import jwt_required

chat_bp = Blueprint("chat", __name__)

MAX_HISTORY = 20


@chat_bp.route("/chat", methods=["POST"])
@jwt_required
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    history = data.get("history") or []

    if not message:
        return jsonify({"error": "message is required"}), 400

    if not isinstance(history, list):
        history = []

    # Keep the normal chat completely separate from the wellness interview.
    safe_history = []
    for item in history[-MAX_HISTORY:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        text = str(item.get("content", item.get("text", ""))).strip()
        if role in ("user", "assistant") and text:
            safe_history.append({"role": role, "content": text})

    reply = generate_general_reply(message, safe_history)
    return jsonify({"reply": reply})
