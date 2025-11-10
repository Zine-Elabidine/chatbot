# ⚡ Déploiement Express sur Render

## 🚀 4 étapes rapides

### 1️⃣ Push sur GitHub

```bash
# Si pas encore initialisé
git init
git add .
git commit -m "Ready for deployment"

# Créez un repo sur github.com, puis :
git remote add origin https://github.com/VOTRE_USERNAME/chatbot.git
git push -u origin main
```

### 2️⃣ Créer le service sur Render

1. Allez sur [render.com](https://render.com) → **Sign Up**
2. Cliquez **New +** → **Web Service**
3. Connectez votre repo GitHub

### 3️⃣ Configuration (1 minute)

| Paramètre | Valeur |
|-----------|--------|
| **Name** | `conso-chatbot` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |

**Variables d'environnement :**

Cliquez **Advanced** → Ajoutez :

```
OPENAI_API_KEY = votre_clé
TAVILY_API_KEY = votre_clé
MODEL_NAME = gpt-4o-mini
TEMPERATURE = 0.7
```

### 4️⃣ Déployer

Cliquez **Create Web Service** → Attendez 3-5 minutes ⏱️

✅ Votre URL : `https://conso-chatbot.onrender.com`

---

## 📧 Message pour le client

```
Salut,

Le chatbot est en ligne : https://conso-chatbot.onrender.com

Note : Premier chargement peut prendre 30s (plan gratuit).
Ensuite ça marche normalement.

Teste et dis-moi ce que tu en penses !
```

---

## 🔄 Mises à jour

```bash
git add .
git commit -m "Amélioration"
git push
```

→ Render redéploie automatiquement ! 🎉
