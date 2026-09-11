import os from flask import Flask, request, jsonify from flask_cors import CORS from google import genai from google.genai import types
app = Flask(name) CORS(app)
SYSTEM_PROMPTS = { "fr": ( "Tu es MOOV IA, un service de questions-reponses par SMS au Burkina Faso, " "sans acces a internet pour l'utilisateur. Reponds TOUJOURS en francais, " "de maniere tres concise (maximum 160 caracteres), simple, directe, utile, " "sans emoji, sans markdown." ), "en": ( "You are MOOV IA, an SMS question-answering service in Burkina Faso, for " "users with no internet access. ALWAYS answer in English, very concisely " "(maximum 160 characters), simple, direct, useful, no emoji, no markdown." ), }
@app.route("/health", methods=["GET"]) def health(): return jsonify({"status": "ok"})
@app.route("/ask", methods=["POST"]) def ask(): api_key = os.environ.get("GEMINI_API_KEY") if not api_key: return jsonify({"error": "Clé API Gemini non configurée dans les variables Render."}), 500
data = request.get_json(silent=True) or {}
question = (data.get("question") or "").strip()
lang = data.get("lang", "fr")
if lang not in SYSTEM_PROMPTS:
    lang = "fr"

if not question:
    return jsonify({"error": "Question vide."}), 400

try:
    # Initialisation du client avec la clé d'environnement
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=question,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPTS[lang],
            max_output_tokens=200,
        )
    )
    
    text = response.text.strip() if response and response.text else ""

    if not text:
        fallback = "Erreur, reessaie." if lang == "fr" else "Error, try again."
        return jsonify({"answer": fallback})

    return jsonify({"answer": text})

except Exception as e:
    app.logger.error(f"Erreur API Gemini: {str(e)}")
    # Affiche le détail de l'erreur dans la réponse pour un diagnostic immédiat
    return jsonify({"error": "Erreur du service IA.", "details": str(e)}), 502
if name == "main": port = int(os.environ.get("PORT", 5000)) app.run(host="0.0.0.0", port=port, debug=False)
