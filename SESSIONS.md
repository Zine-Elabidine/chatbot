# 💾 Système de Sessions avec Historique

Documentation du système de gestion de sessions temporaires pour le chatbot Conso News.

## 🎯 Fonctionnement

Le système utilise des **sessions temporaires en mémoire** qui permettent de conserver l'historique des conversations sans base de données ni comptes utilisateurs.

### Caractéristiques

- ✅ **Session ID unique** généré automatiquement (UUID)
- ✅ **Stockage en mémoire** - rapide et simple
- ✅ **Expiration automatique** - 30 minutes d'inactivité (configurable)
- ✅ **Nettoyage automatique** - suppression des sessions expirées
- ✅ **Thread-safe** - utilisation de locks pour éviter les conflits
- ✅ **Sans base de données** - parfait pour un projet weekend

## 🔄 Flux de travail

### 1. Création de session

```javascript
// L'utilisateur ouvre la page
POST /session/new

// Réponse
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Session créée avec succès"
}
```

### 2. Chat avec historique

```javascript
// Envoyer un message avec session_id
POST /session/chat
{
  "message": "Quelles sont les dernières actualités sur les smartphones?",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}

// Réponse avec session_id et compteur
{
  "response": "Voici les dernières actualités...",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message_count": 2,
  "success": true
}
```

### 3. Gestion automatique

- **Sans session_id**: Une nouvelle session est créée automatiquement
- **Session expirée**: Une nouvelle session est créée automatiquement
- **Session valide**: L'historique est préservé et utilisé

## 📡 Endpoints disponibles

### `POST /session/new`
Crée une nouvelle session de chat.

**Réponse:**
```json
{
  "session_id": "uuid",
  "message": "Session créée avec succès"
}
```

### `POST /session/chat`
Chat avec gestion automatique de l'historique.

**Requête:**
```json
{
  "message": "Votre question",
  "session_id": "uuid-optionnel"
}
```

**Réponse:**
```json
{
  "response": "Réponse du chatbot",
  "session_id": "uuid",
  "message_count": 5,
  "success": true
}
```

### `GET /session/{session_id}/info`
Récupère les informations d'une session.

**Réponse:**
```json
{
  "session_id": "uuid",
  "message_count": 10,
  "created_at": "2025-11-08T14:30:00",
  "last_activity": "2025-11-08T14:45:00",
  "expires_in_minutes": 25
}
```

### `DELETE /session/{session_id}`
Supprime une session (réinitialisation de conversation).

**Réponse:**
```json
{
  "message": "Session supprimée avec succès"
}
```

### `GET /sessions/stats`
Statistiques des sessions actives.

**Réponse:**
```json
{
  "active_sessions": 42
}
```

## 💻 Utilisation côté client

### JavaScript (Frontend)

```javascript
let sessionId = null;

// 1. Créer ou charger une session
async function initSession() {
    // Vérifier localStorage
    const savedId = localStorage.getItem('chatbot_session_id');
    
    if (savedId) {
        // Vérifier si valide
        const response = await fetch(`/session/${savedId}/info`);
        if (response.ok) {
            sessionId = savedId;
            return;
        }
    }
    
    // Créer nouvelle session
    const response = await fetch('/session/new', { method: 'POST' });
    const data = await response.json();
    sessionId = data.session_id;
    localStorage.setItem('chatbot_session_id', sessionId);
}

// 2. Envoyer un message
async function sendMessage(message) {
    const response = await fetch('/session/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            message: message,
            session_id: sessionId 
        })
    });
    
    const data = await response.json();
    console.log(data.response);
    console.log(`Messages dans la session: ${data.message_count}`);
}
```

### Python (Client API)

```python
import requests

class ChatbotClient:
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
        self.session_id = None
    
    def create_session(self):
        """Crée une nouvelle session."""
        response = requests.post(f"{self.api_url}/session/new")
        data = response.json()
        self.session_id = data["session_id"]
        return self.session_id
    
    def chat(self, message):
        """Envoie un message et reçoit une réponse."""
        if not self.session_id:
            self.create_session()
        
        response = requests.post(
            f"{self.api_url}/session/chat",
            json={
                "message": message,
                "session_id": self.session_id
            }
        )
        data = response.json()
        return data["response"]
    
    def reset(self):
        """Réinitialise la conversation."""
        if self.session_id:
            requests.delete(f"{self.api_url}/session/{self.session_id}")
        self.create_session()

# Utilisation
client = ChatbotClient()
print(client.chat("Bonjour!"))
print(client.chat("Quelles sont les dernières actualités?"))
client.reset()  # Nouvelle conversation
```

## 🔧 Configuration

### Modifier la durée d'expiration

Dans `session_manager.py`:

```python
# Changer la durée d'expiration (en minutes)
session_manager = SessionManager(session_timeout_minutes=60)  # 1 heure
```

### Fréquence de nettoyage

Dans `session_manager.py`, méthode `_cleanup_expired_sessions()`:

```python
time.sleep(600)  # Vérifier toutes les 10 minutes au lieu de 5
```

## 🎭 Cas d'usage

### 1. Interface web simple
- Session stockée dans `localStorage`
- Persistance entre rechargements de page
- Expiration après 30 minutes d'inactivité

### 2. Widget WordPress
- Création de session au chargement du widget
- Session par visiteur (sans authentification)
- Historique conservé pendant la visite

### 3. API externe
- Client peut créer et gérer ses sessions
- Multiples conversations parallèles possibles
- Session ID transmis à chaque requête

## ⚠️ Limitations

### Stockage en mémoire
- ❌ Les sessions sont perdues au redémarrage du serveur
- ❌ Non adapté pour un grand volume de sessions simultanées
- ❌ Pas de persistance entre serveurs (si load balancing)

### Solutions alternatives pour la production

**Si vous avez besoin de persistance:**

1. **Redis** - Cache en mémoire distribué
   ```python
   pip install redis
   # Utiliser Redis au lieu du dict en mémoire
   ```

2. **Base de données** - PostgreSQL, MongoDB
   ```python
   # Stocker les sessions et historiques en DB
   ```

3. **Session cookies** - FastAPI sessions
   ```python
   pip install fastapi-sessions
   # Sessions côté serveur avec cookies
   ```

## 🔐 Sécurité

### Bonnes pratiques

- ✅ Session ID généré avec UUID4 (sécurisé)
- ✅ Expiration automatique (limite la mémoire utilisée)
- ✅ Pas de données sensibles stockées
- ✅ Thread-safe avec locks

### Pour la production

- 🔒 Limiter le nombre de sessions par IP
- 🔒 Ajouter rate limiting
- 🔒 Valider le format du session_id
- 🔒 Logger les activités suspectes
- 🔒 Utiliser HTTPS

## 📊 Monitoring

### Vérifier les sessions actives

```bash
curl http://localhost:8000/sessions/stats
```

### Informations d'une session

```bash
curl http://localhost:8000/session/{session_id}/info
```

## 🆘 Dépannage

### Session perdue après rechargement
- Vérifiez que `localStorage` fonctionne
- Vérifiez que le session_id est valide
- Session peut avoir expiré (30 min d'inactivité)

### Trop de mémoire utilisée
- Réduire `session_timeout_minutes`
- Augmenter la fréquence de nettoyage
- Considérer Redis pour stockage externe

### Sessions ne s'expirent pas
- Vérifier que le thread de nettoyage tourne
- Vérifier les logs de nettoyage automatique

## 📝 Exemple complet

```bash
# 1. Créer une session
curl -X POST http://localhost:8000/session/new

# Réponse: {"session_id": "xxx", "message": "..."}

# 2. Chat avec historique
curl -X POST http://localhost:8000/session/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Bonjour!", "session_id": "xxx"}'

# 3. Continuer la conversation (avec contexte)
curl -X POST http://localhost:8000/session/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Et après?", "session_id": "xxx"}'

# 4. Vérifier la session
curl http://localhost:8000/session/xxx/info

# 5. Supprimer la session
curl -X DELETE http://localhost:8000/session/xxx
```

## 🎉 Avantages

- ✅ **Simple** - Pas de base de données nécessaire
- ✅ **Rapide** - Tout en mémoire
- ✅ **Léger** - Parfait pour un projet weekend
- ✅ **Flexible** - Facile à étendre
- ✅ **Automatique** - Gestion transparente pour l'utilisateur

Parfait pour un chatbot sans comptes utilisateurs! 🚀
