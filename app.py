"""
MOOV IA — Serveur relais Flask
Reçoit les questions du frontend HTML, appelle l'API Gemini côté serveur
(hors des restrictions géographiques et sans exposer la clé API au client),
et renvoie la réponse SMS-friendly (~160 caractères).
"""

import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Autorise les appels depuis le frontend HTML (à restreindre en prod, cf. note plus bas)

# La clé est lue depuis une variable d'environnement — jamais codée en dur, jamais exposée au client
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

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
    if not GEMINI_API_KEY:
        return jsonify({"error": "Clé API Gemini non configurée côté serveur."}), 500

    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    lang = data.get("lang", "fr")
    if lang not in SYSTEM_PROMPTS:
        lang = "fr"

    if not question:
        return jsonify({"error": "Question vide."}), 400

    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPTS[lang]}]},
        "contents": [{"role": "user", "parts": [{"text": question}]}],
        "generationConfig": {"maxOutputTokens": 200},
    }

    try:
        resp = requests.post(
            GEMINI_URL,
            params={"key": GEMINI_API_KEY},
            json=payload,
            timeout=20,
        )
        resp.raise_for_status()
        result = resp.json()
        candidates = result.get("candidates", [])
        text = ""
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            text = "".join(p.get("text", "") for p in parts).strip()

        if not text:
            fallback = "Erreur, reessaie." if lang == "fr" else "Error, try again."
            return jsonify({"answer": fallback})

        return jsonify({"answer": text})

    except requests.exceptions.RequestException as e:
        app.logger.error(f"Erreur appel Gemini: {e}")
        msg = "Erreur du service IA. Réessaie plus tard." if lang == "fr" else "AI service error. Try again later."
        return jsonify({"error": msg}), 502


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
