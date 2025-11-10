# 🤖 Chatbot Conso News

Chatbot intelligent pour la plateforme Conso News avec capacités de recherche web et réponses en français.

## 🚀 Caractéristiques

- **Agent LangGraph** avec LLM au choix (compatible OpenAI)
- **Support multi-LLM**: OpenAI, Gemini, ou n'importe quel LLM compatible OpenAI
- **Recherche web en temps réel** via Tavily
- **Rendu Markdown complet** - Tables, listes, code, etc. pour des comparatifs structurés
- **API REST FastAPI** pour intégration facile
- **Réponses en français** optimisées pour l'actualité et la consommation
- **Support CORS** pour intégration WordPress
- **Historique de conversation** pour contexte multi-tours
- **Sessions temporaires** (30 min) sans comptes utilisateurs
- **Contexte temporel** - Le chatbot connaît la date/heure UTC actuelle

## 📋 Prérequis

- Python 3.9+
- Clés API:
  - **LLM API Key** (OpenAI, Gemini, ou autre fournisseur compatible OpenAI)
  - **Tavily API Key** (gratuit sur https://tavily.com)

## 🛠️ Installation

1. **Cloner ou télécharger le projet**

2. **Créer un environnement virtuel**
```bash
python -m venv venv
```

3. **Activer l'environnement virtuel**
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

4. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

5. **Configurer les variables d'environnement**
```bash
# Copier le fichier exemple
copy .env.example .env

# Éditer .env et configurer:
```

**Variables requises dans `.env`:**
```env
# Pour OpenAI (défaut)
LLM_API_KEY=sk-your-openai-api-key
LLM_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-4o-mini

# Pour Gemini (OpenAI-compatible)
LLM_API_KEY=your-gemini-api-key
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
MODEL_NAME=gemini-1.5-flash

# Pour tout autre LLM compatible OpenAI
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://your-llm-provider.com/v1
MODEL_NAME=your-model-name

# Recherche web (requis)
TAVILY_API_KEY=tvly-your-tavily-api-key
```

## ▶️ Lancement

```bash
python main.py
```

Le serveur démarre sur `http://localhost:8000`

## 📡 Endpoints API

### Endpoints de base

#### `GET /`
Point d'entrée principal avec message de bienvenue.

#### `GET /health`
Vérification de l'état de santé du service.

#### `POST /chat/simple`
Endpoint simplifié sans historique pour des requêtes rapides.

**Requête:**
```json
{
  "message": "Compare les prix des iPhone 15"
}
```

### 💾 Endpoints avec Sessions (Recommandé)

Le système de sessions permet de conserver l'historique des conversations temporairement (30 min) sans comptes utilisateurs.

#### `POST /session/new`
Crée une nouvelle session de chat.

**Réponse:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Session créée avec succès"
}
```

#### `POST /session/chat`
Chat avec historique automatique via session.

**Requête:**
```json
{
  "message": "Quelles sont les dernières actualités sur les smartphones?",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Réponse:**
```json
{
  "response": "Voici les dernières actualités...",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message_count": 5,
  "success": true
}
```

#### `GET /session/{session_id}/info`
Récupère les informations d'une session.

#### `DELETE /session/{session_id}`
Supprime une session (réinitialisation).

#### `GET /sessions/stats`
Statistiques des sessions actives.

📖 **Documentation complète**: Voir [SESSIONS.md](SESSIONS.md)

### Legacy: POST /chat
Endpoint manuel avec historique (vous devez gérer l'historique côté client).

## 🧪 Test rapide

```bash
# Test avec curl
curl -X POST "http://localhost:8000/chat/simple" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Quelles sont les meilleures offres pour un ordinateur portable?\"}"
```

Ou utiliser le script de test fourni:
```bash
python test_chatbot.py
```

## 🔧 Configuration

### Variables d'environnement (`.env`)
- `LLM_API_KEY`: Clé API de votre fournisseur LLM
- `LLM_BASE_URL`: URL de base de l'API (compatible OpenAI)
- `MODEL_NAME`: Nom du modèle à utiliser (défaut: gpt-4o-mini)
- `TEMPERATURE`: Créativité du modèle 0-1 (défaut: 0.7)
- `TAVILY_API_KEY`: Clé API Tavily pour la recherche web

### Configuration avancée (`config.py`)
- Personnaliser le prompt système (`SYSTEM_PROMPT`)
- Modifier les paramètres par défaut

## 📦 Structure du projet

```
chatbot/
├── main.py                   # Application FastAPI avec endpoints
├── agent.py                  # Agent LangGraph avec recherche web
├── config.py                 # Configuration et prompts en français
├── session_manager.py        # Gestionnaire de sessions temporaires
├── requirements.txt          # Dépendances Python
├── .env                      # Variables d'environnement (à créer)
├── .env.example              # Exemple de configuration
├── index.html                # Interface web avec rendu markdown
├── wordpress_integration.js  # Widget WordPress complet
├── test_chatbot.py           # Script de test basique
├── test_sessions.py          # Script de test des sessions
├── README.md                 # Documentation principale
├── SESSIONS.md               # Documentation système de sessions
├── MARKDOWN_RENDERING.md     # Guide rendu markdown et tables
├── CHANGELOG.md              # Historique des changements
└── GEMINI_SETUP.md           # Guide configuration Gemini
```

## 🌐 Intégration WordPress

Pour intégrer avec WordPress:

1. **Plugin Custom HTML/JavaScript** ou créer un plugin personnalisé
2. **Faire des requêtes AJAX** vers l'API:

```javascript
async function askChatbot(message) {
  const response = await fetch('http://votre-serveur:8000/chat/simple', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message: message })
  });
  
  const data = await response.json();
  return data.response;
}
```

## 🔐 Sécurité

**Important pour la production:**
- Restreindre CORS aux domaines spécifiques
- Ajouter une authentification API
- Utiliser HTTPS
- Limiter le rate limiting
- Ne jamais exposer les clés API

## 📝 Prochaines étapes

- [ ] Intégration avec WordPress (ingestion de données)
- [ ] Base de données vectorielle pour les articles
- [ ] Cache des réponses fréquentes
- [ ] Interface web pour tester
- [ ] Monitoring et logs
- [ ] Déploiement sur serveur cloud

## 🆘 Support

Pour toute question ou problème, vérifiez:
1. Les clés API sont correctement configurées dans `.env`
2. Toutes les dépendances sont installées
3. Le port 8000 est disponible

## 📄 License

Projet personnel - Tous droits réservés
