# ✅ Checklist de Déploiement

## Avant de déployer

- [ ] Les clés API sont prêtes (OPENAI_API_KEY, TAVILY_API_KEY)
- [ ] Le code est testé localement (`python main.py`)
- [ ] Le fichier `.env` n'est PAS commité (vérifié dans `.gitignore`)
- [ ] `requirements.txt` est à jour

## Étapes GitHub

- [ ] Code committé : `git add . && git commit -m "Ready for deployment"`
- [ ] Repository créé sur github.com
- [ ] Code pushé : `git push origin main`

## Étapes Render

- [ ] Compte créé sur render.com
- [ ] GitHub connecté à Render
- [ ] Web Service créé avec le bon repo
- [ ] Build command : `pip install -r requirements.txt`
- [ ] Start command : `uvicorn main:app --host 0.0.0.0 --port $PORT`
- [ ] Variables d'environnement ajoutées :
  - [ ] OPENAI_API_KEY
  - [ ] TAVILY_API_KEY
  - [ ] OPENAI_API_BASE (si nécessaire)
  - [ ] MODEL_NAME (optionnel)
  - [ ] TEMPERATURE (optionnel)
- [ ] Service déployé (attendre 3-5 min)

## Tests post-déploiement

- [ ] URL fonctionne : `https://votre-app.onrender.com`
- [ ] Page d'accueil charge le chatbot
- [ ] API health : `https://votre-app.onrender.com/health` répond
- [ ] Test d'un message dans le chatbot
- [ ] Test de recherche web (si utilisé)
- [ ] Test de reset conversation

## Partage avec le client

- [ ] URL partagée
- [ ] Note sur les 30s de démarrage (plan gratuit)
- [ ] Instructions d'utilisation envoyées

---

## 🎉 C'est fait !

Votre chatbot est en ligne et prêt pour les tests !
