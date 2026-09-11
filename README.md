# MOOV IA — Serveur relais Gemini

Ce petit serveur Flask évite deux problèmes :
1. La clé API Gemini n'est plus exposée dans le HTML (elle reste sur le serveur).
2. L'appel à Gemini se fait depuis le serveur (région du serveur), ce qui contourne
   les éventuelles restrictions géographiques rencontrées côté client au Burkina Faso.

## Test en local

```bash
cd moov-ia-relay
pip install -r requirements.txt

# Sur Mac/Linux :
export GEMINI_API_KEY="ta_cle_ici"
# Sur Windows (PowerShell) :
$env:GEMINI_API_KEY="ta_cle_ici"

python app.py
```

Le serveur tourne sur http://localhost:5000
Ouvre ensuite `moov-ia-relay.html` dans ton navigateur (le RELAY_URL est déjà
configuré sur localhost:5000).

Teste que le serveur répond :
```bash
curl http://localhost:5000/health
```

## Déploiement sur Render (comme Mon Foyer)

1. Pousse ce dossier dans un repo Git (GitHub par ex.)
2. Sur Render : New > Web Service, connecte le repo
3. Build command : `pip install -r requirements.txt`
4. Start command : `gunicorn app:app`
5. Dans les variables d'environnement Render, ajoute `GEMINI_API_KEY` avec ta clé
6. Une fois déployé, récupère l'URL Render (ex: `https://moov-ia-relay.onrender.com`)
7. Dans `moov-ia-relay.html`, remplace la ligne :
   ```js
   const RELAY_URL = "http://localhost:5000/ask";
   ```
   par :
   ```js
   const RELAY_URL = "https://moov-ia-relay.onrender.com/ask";
   ```

## Sécurité à ajuster avant une vraie mise en prod

- `CORS(app)` autorise actuellement toutes les origines — à restreindre au domaine
  final du frontend une fois celui-ci fixé (`CORS(app, origins=["https://tondomaine.com"])`).
- Pense à limiter le débit de requêtes (rate limiting) pour éviter les abus sur ta clé Gemini.
- La clé API Gemini que tu m'as partagée dans le chat a été vue en clair dans la
  conversation — envisage de la régénérer sur Google AI Studio avant la mise en prod.
