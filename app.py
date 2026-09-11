"""
MOOV IA — Serveur relais Flask
Reçoit les questions du frontend HTML, appelle l'API Groq côté serveur
(sans exposer la clé API au client), et renvoie la réponse SMS-friendly (~160 caractères).
"""

import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)

SYSTEM_PROMPTS = {
    "fr": (
        "Tu es MOOV IA, un service de questions-reponses par SMS au Burkina Faso, "
        "sans acces a internet pour l'utilisateur. Reponds TOUJOURS en francais, "
        "de maniere tres concise (maximum 160 caracteres), simple, directe, utile, "
        "sans emoji, sans markdown."
    ),
    "en": (
        "You are MOOV IA, an SMS question-answering service in Burkina Faso, for "
        "users with no internet access. ALWAYS answer in English, very concisely "
        "(maximum 160 characters), simple, direct, useful, no emoji, no markdown."
    ),
}


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/ask", methods=["POST"])
def ask():
    if not GROQ_API_KEY:
        return jsonify({"error": "Clé API Groq non configurée côté serveur."}), 500

    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    lang = data.get("lang", "fr")
    if lang not in SYSTEM_PROMPTS:
        lang = "fr"

    if not question:
        return jsonify({"error": "Question vide."}), 400

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPTS[lang]},
                {"role": "user", "content": question},
            ],
            max_tokens=200,
            timeout=20,
        )
        text = (response.choices[0].message.content or "").strip()

        if not text:
            fallback = "Erreur, reessaie." if lang == "fr" else "Error, try again."
            return jsonify({"answer": fallback})

        return jsonify({"answer": text})

    except Exception as e:
        app.logger.error(f"Erreur appel Groq: {e}")
        msg = "Erreur du service IA. Réessaie plus tard." if lang == "fr" else "AI service error. Try again later."
        return jsonify({"error": msg}), 502


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
