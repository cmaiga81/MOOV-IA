import os import requests from flask import Flask, request, jsonify from flask_cors import CORS
app = Flask(name) CORS(app)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
Utilisation du modèle flash stable
GEMINI_MODEL = "gemini-1.5-flash" GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
SYSTEM_PROMPTS = { "fr": ( "Tu es MOOV IA, un service de questions-reponses par SMS au Burkina Faso, " "sans acces a internet pour l'utilisateur. Reponds TOUJOURS en francais, " "de maniere tres concise (maximum 160 caracteres), simple, directe, utile, " "sans emoji, sans markdown." ), "en": ( "You are MOOV IA, an SMS question-answering service in Burkina Faso, for " "users with no internet access. ALWAYS answer in English, very concisely " "(maximum 160 characters), simple, direct, useful, no emoji, no markdown." ), }
@app.route("/health", methods=["GET"]) def health(): return jsonify({"status": "ok"})
@app.route("/ask", methods=["POST"]) def ask(): if not GEMINI_API_KEY: return jsonify({"error": "Clé API non configurée."}), 500
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
        params={"key": GEMINI_API_KEY.strip()},
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

    return jsonify({"answer": text or "Erreur, reessaie."})

except requests.exceptions.RequestException as e:
    error_detail = ""
    if e.response is not None:
        error_detail = f" (Code: {e.response.status_code} - {e.response.text})"
    app.logger.error(f"Erreur Gemini: {e}{error_detail}")
    return jsonify({"error": f"Erreur du service IA{error_detail}"}), 502
if name == "main": port = int(os.environ.get("PORT", 5000)) app.run(host="0.0.0.0", port=port, debug=False)
