# 🚀 Guide de Déploiement Render

Ce guide explique comment déployer le chatbot Conso News sur Render.

## 📋 Prérequis

1. **Compte GitHub** (gratuit)
2. **Compte Render** (gratuit) - [render.com](https://render.com)
3. **Clés API** :
   - OpenAI API Key (ou autre LLM compatible)
   - Tavily API Key

---

## 🔧 Étape 1 : Préparer le code pour GitHub

### 1.1 Initialiser Git (si ce n'est pas déjà fait)

```bash
cd c:\Users\sekera\Desktop\chatbot
git init
```

### 1.2 Créer un fichier `.gitignore`

Assurez-vous d'avoir un `.gitignore` pour ne pas exposer vos clés :

```
.env
__pycache__/
*.pyc
*.pyo
.venv/
venv/
.DS_Store
.vscode/
*.log
```

### 1.3 Commit et Push sur GitHub

```bash
git add .
git commit -m "Initial commit - Conso News Chatbot"

# Créez un nouveau repo sur github.com, puis :
git remote add origin https://github.com/VOTRE_USERNAME/chatbot-conso-news.git
git branch -M main
git push -u origin main
```

---

## 🌐 Étape 2 : Déployer sur Render

### 2.1 Se connecter à Render

1. Allez sur [render.com](https://render.com)
2. Cliquez sur **Sign Up** (ou Sign In si vous avez déjà un compte)
3. Connectez votre compte GitHub

### 2.2 Créer un nouveau Web Service

1. Dans le dashboard Render, cliquez sur **New +**
2. Sélectionnez **Web Service**
3. Connectez votre repository GitHub `chatbot-conso-news`
4. Cliquez sur **Connect**

### 2.3 Configuration du Service

Remplissez les champs suivants :

| Champ | Valeur |
|-------|--------|
| **Name** | `conso-news-chatbot` |
| **Region** | Europe (Paris) ou le plus proche |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |

### 2.4 Plan

- Sélectionnez **Free** (gratuit)

### 2.5 Variables d'environnement

Cliquez sur **Advanced** puis ajoutez ces variables :

| Key | Value | Notes |
|-----|-------|-------|
| `OPENAI_API_KEY` | `sk-...` | Votre clé OpenAI |
| `TAVILY_API_KEY` | `tvly-...` | Votre clé Tavily |
| `OPENAI_API_BASE` | `https://api.openai.com/v1` | Ou autre si vous utilisez un autre LLM |
| `MODEL_NAME` | `gpt-4o-mini` | Ou autre modèle |
| `TEMPERATURE` | `0.7` | Optionnel |

### 2.6 Lancer le déploiement

1. Cliquez sur **Create Web Service**
2. Render va automatiquement :
   - Cloner votre repo
   - Installer les dépendances
   - Démarrer votre application
3. ⏱️ Attendez 2-5 minutes

---

## ✅ Étape 3 : Tester le déploiement

### 3.1 Obtenir l'URL

Une fois déployé, Render vous donne une URL comme :
```
https://conso-news-chatbot.onrender.com
```

### 3.2 Vérifier que ça marche

1. **Ouvrez l'URL dans votre navigateur**
   - Vous devriez voir l'interface du chatbot

2. **Testez l'API**
   - Allez sur `https://votre-app.onrender.com/health`
   - Vous devriez voir : `{"status":"healthy","message":"Le service est opérationnel"}`

3. **Testez le chatbot**
   - Envoyez un message depuis l'interface
   - Si ça répond → ✅ Tout fonctionne !

---

## 🔄 Étape 4 : Mises à jour automatiques

À chaque fois que vous push sur GitHub :

```bash
git add .
git commit -m "Amélioration du chatbot"
git push
```

Render va **automatiquement redéployer** votre application ! 🎉

---

## ⚠️ Points importants

### Free Tier Limitations

- ✅ **Gratuit** pour toujours
- ⏸️ **Se met en veille** après 15 minutes d'inactivité
- 🔄 **Réveille en ~30 secondes** à la première requête
- 💾 **750 heures/mois** (suffisant pour testing et petite production)

### Pour garder toujours actif (optionnel)

Upgrade vers le plan payant ($7/mois) pour :
- Pas de mise en veille
- Plus de ressources
- Meilleure performance

---

## 🐛 Dépannage

### Le déploiement échoue

1. **Vérifiez les logs** dans Render Dashboard
2. **Erreur de dépendances** : Assurez-vous que `requirements.txt` est correct
3. **Erreur au démarrage** : Vérifiez que les variables d'environnement sont bien définies

### Le chatbot ne répond pas

1. **Vérifiez les variables d'environnement** dans Render
2. **Vérifiez les logs** pour voir les erreurs API
3. **Testez l'endpoint** `/health` pour voir si l'API est up

### Service en veille

- C'est normal sur le plan gratuit
- Le service se réveille automatiquement à la première requête
- Pour l'éviter : upgrade vers plan payant OU utilisez un service de "ping" gratuit

---

## 📱 Partager avec le client

Envoyez simplement l'URL à votre client :

```
Bonjour,

Voici le chatbot Conso News déployé pour vos tests :
👉 https://conso-news-chatbot.onrender.com

Notes :
- L'application peut prendre ~30 secondes à démarrer si non utilisée récemment (plan gratuit)
- Une fois chargée, elle fonctionne normalement
- Testez les différentes fonctionnalités (recherche web, comparaisons, etc.)

N'hésitez pas à me faire vos retours !
```

---

## 🎯 C'est tout !

Votre chatbot est maintenant **en ligne** et **accessible mondialement** ! 🌍

Pour toute question, consultez la [documentation Render](https://render.com/docs).
