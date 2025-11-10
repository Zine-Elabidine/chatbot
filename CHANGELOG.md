# 📝 Changelog - Mises à jour du chatbot

## 🆕 Nouveautés ajoutées

### 1. Bouton de réinitialisation de conversation

#### Interface web (`index.html`)
- ✅ Bouton "🔄 Nouvelle conversation" dans le header
- ✅ Fonction `resetConversation()` qui:
  - Supprime la session actuelle via l'API
  - Nettoie le localStorage
  - Vide l'affichage du chat
  - Crée une nouvelle session automatiquement
- ✅ Confirmation avant réinitialisation
- ✅ Design responsive et intégré

#### Widget WordPress (`wordpress_integration.js`)
- ✅ Bouton "🔄" dans le header du widget
- ✅ Méthode `resetConversation()` dans la classe
- ✅ Styles CSS pour le bouton
- ✅ Event listener configuré

### 2. Contexte temporel dans le système

#### Configuration dynamique du prompt (`config.py`)
- ✅ Nouvelle fonction `get_system_prompt()` qui génère le prompt avec:
  - **Date actuelle en français** (ex: "Vendredi 08 novembre 2025")
  - **Heure actuelle UTC** (ex: "14:30 UTC")
  - Traduction automatique des jours et mois en français
- ✅ Le prompt est régénéré à chaque requête pour avoir l'heure exacte

#### Agent mis à jour (`agent.py`)
- ✅ Import de `get_system_prompt()` au lieu de `SYSTEM_PROMPT` statique
- ✅ Méthode `_call_model()` utilise `get_system_prompt()` dynamiquement
- ✅ Le chatbot reçoit toujours le contexte temporel actuel

## 📋 Exemple de prompt système généré

```
Tu es un assistant intelligent pour Conso News, une plateforme d'actualités et de consommation.

CONTEXTE TEMPOREL:
Nous sommes le Vendredi 08 novembre 2025, il est 14:22 UTC.
Utilise cette information pour contextualiser tes réponses et recherches.

Ton rôle est d'aider les utilisateurs en:
1. Répondant aux questions sur l'actualité et les nouvelles
2. Recherchant des informations en ligne quand nécessaire
3. Fournissant des informations sur les marques et produits
4. Aidant à comparer des offres et des prix
...
```

## 🎯 Avantages

### Bouton de réinitialisation
- ✅ **Expérience utilisateur améliorée** - Permet de repartir de zéro facilement
- ✅ **Gestion propre des sessions** - Suppression côté serveur et client
- ✅ **Intuitif** - Bouton visible et accessible
- ✅ **Confirmation** - Évite les réinitialisations accidentelles

### Contexte temporel
- ✅ **Chatbot conscient du temps** - Peut référencer la date et l'heure actuelles
- ✅ **Meilleure pertinence** - Comprend "aujourd'hui", "cette semaine", etc.
- ✅ **Recherches contextuelles** - Peut chercher des infos récentes
- ✅ **Dynamique** - L'heure est mise à jour à chaque requête

## 🧪 Comment tester

### Test du bouton de réinitialisation

```bash
# 1. Lancer le serveur
python main.py

# 2. Ouvrir index.html dans le navigateur

# 3. Tester:
- Envoyez quelques messages
- Cliquez sur "🔄 Nouvelle conversation"
- Confirmez
- La conversation est réinitialisée ✅
```

### Test du contexte temporel

Demandez au chatbot:
- "Quelle heure est-il?"
- "Quel jour sommes-nous?"
- "On est quel mois?"
- "Quelle est la date d'aujourd'hui?"

Le chatbot devrait connaître la date et l'heure UTC actuelles! 🎉

## 📁 Fichiers modifiés

```
✏️ Modifiés:
├── config.py              - Fonction get_system_prompt() avec date/heure UTC
├── agent.py               - Utilise get_system_prompt() dynamiquement
├── index.html             - Bouton reset + fonction resetConversation()
└── wordpress_integration.js - Bouton reset dans le widget WordPress

📄 Nouveau:
└── CHANGELOG.md           - Ce fichier
```

## 🔍 Détails techniques

### Génération de la date/heure

```python
from datetime import datetime

now_utc = datetime.utcnow()
date_str = now_utc.strftime("%A %d %B %Y")  # Friday 08 November 2025
time_str = now_utc.strftime("%H:%M UTC")     # 14:22 UTC

# Traduction en français
jours = {'Monday': 'Lundi', 'Tuesday': 'Mardi', ...}
mois = {'January': 'janvier', 'February': 'février', ...}
```

### Réinitialisation de conversation

```javascript
async function resetConversation() {
    // 1. Confirmer l'action
    if (!confirm('Voulez-vous vraiment recommencer?')) return;
    
    // 2. Supprimer la session via API
    await fetch(`${API_URL}/session/${sessionId}`, { method: 'DELETE' });
    
    // 3. Nettoyer localStorage
    localStorage.removeItem('chatbot_session_id');
    
    // 4. Vider l'affichage
    chatContainer.innerHTML = '...';
    
    // 5. Créer nouvelle session
    await initSession();
}
```

## 💡 Cas d'usage

### Avec contexte temporel

**Utilisateur:** "Quelles sont les actualités d'aujourd'hui?"
**Chatbot:** Sait qu'on est le 8 novembre 2025 ✅

**Utilisateur:** "Quelle heure est-il?"
**Chatbot:** "Il est actuellement 14:22 UTC" ✅

**Utilisateur:** "C'est quel jour aujourd'hui?"
**Chatbot:** "Nous sommes vendredi 8 novembre 2025" ✅

### Avec bouton de réinitialisation

- ❌ Conversation partie dans une mauvaise direction → Clic sur 🔄
- ❌ Trop de contexte accumulé → Clic sur 🔄
- ❌ Veut changer de sujet complètement → Clic sur 🔄
- ✅ Nouvelle conversation propre instantanément

## 🚀 Prochaines améliorations possibles

- [ ] Ajouter le fuseau horaire de l'utilisateur (au lieu d'UTC)
- [ ] Historique des sessions (liste des conversations passées)
- [ ] Export de conversation
- [ ] Mode sombre/clair
- [ ] Personnalisation du chatbot

## ✅ État actuel

Le chatbot Conso News dispose maintenant de:
- ✅ Gestion de sessions temporaires (30 min)
- ✅ Historique de conversation automatique
- ✅ Bouton de réinitialisation dans l'interface
- ✅ Connaissance de la date et l'heure actuelles (UTC)
- ✅ Recherche web avec Tavily
- ✅ Support multi-LLM (OpenAI, Gemini, etc.)
- ✅ Interface web élégante et responsive
- ✅ Widget WordPress prêt à l'emploi

Prêt pour la production! 🎉
