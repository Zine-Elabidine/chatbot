# 🔷 Configuration Gemini

Guide rapide pour utiliser Google Gemini avec le chatbot Conso News.

## 📋 Étapes de configuration

### 1. Obtenir une clé API Gemini

1. Allez sur [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Connectez-vous avec votre compte Google
3. Cliquez sur "Get API Key" ou "Create API Key"
4. Copiez votre clé API

### 2. Configurer le fichier `.env`

Ouvrez le fichier `.env` et ajoutez:

```env
# Configuration Gemini
LLM_API_KEY=votre_cle_api_gemini
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
MODEL_NAME=gemini-1.5-flash
TEMPERATURE=0.7

# Recherche Web (Tavily)
TAVILY_API_KEY=votre_cle_tavily
```

### 3. Modèles Gemini disponibles

Via l'endpoint OpenAI-compatible, vous pouvez utiliser:

- `gemini-1.5-flash` - Rapide et économique (recommandé)
- `gemini-1.5-pro` - Plus puissant, meilleure qualité
- `gemini-2.0-flash-exp` - Version expérimentale la plus récente

### 4. Lancer l'application

```bash
python main.py
```

## 🔍 Vérification

Pour vérifier que tout fonctionne:

```bash
# Test simple
curl -X POST "http://localhost:8000/chat/simple" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Bonjour, peux-tu te présenter?\"}"
```

Ou utilisez le script de test:
```bash
python test_chatbot.py
```

## ⚠️ Notes importantes

### Limitations connues

1. **Endpoint OpenAI-compatible**: Gemini via cet endpoint peut avoir des limitations par rapport à l'API native Gemini
2. **Tool calling**: Assurez-vous que votre version de Gemini supporte le tool/function calling
3. **Rate limits**: Respectez les limites de taux de Google

### Alternative: Utiliser Gemini nativement

Si l'endpoint OpenAI-compatible ne fonctionne pas bien, vous pouvez:

1. Installer le SDK Gemini: `pip install langchain-google-genai`
2. Modifier `agent.py` pour utiliser `ChatGoogleGenerativeAI` au lieu de `ChatOpenAI`

Exemple de modification dans `agent.py`:
```python
from langchain_google_genai import ChatGoogleGenerativeAI

# Dans __init__:
self.llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    temperature=TEMPERATURE,
    google_api_key=LLM_API_KEY
)
```

## 💡 Conseils

- **Pour le développement**: Utilisez `gemini-1.5-flash` (gratuit et rapide)
- **Pour la production**: Considérez `gemini-1.5-pro` pour de meilleurs résultats
- **Budget**: Gemini offre un tier gratuit généreux pour tester

## 🆘 Dépannage

### Erreur: "Invalid API Key"
- Vérifiez que votre clé API est correcte
- Assurez-vous que l'API Gemini est activée dans votre projet Google Cloud

### Erreur: "Model not found"
- Vérifiez le nom du modèle (sensible à la casse)
- Certains modèles peuvent ne pas être disponibles via l'endpoint OpenAI-compatible

### Erreur de tool calling
- Essayez avec `gemini-1.5-flash` ou `gemini-1.5-pro` qui supportent bien les function calls
- Si le problème persiste, utilisez l'API native Gemini (voir section Alternative)

## 📚 Ressources

- [Google AI Studio](https://aistudio.google.com/)
- [Documentation Gemini API](https://ai.google.dev/docs)
- [Tarification Gemini](https://ai.google.dev/pricing)
- [Limites de taux](https://ai.google.dev/gemini-api/docs/quota)
