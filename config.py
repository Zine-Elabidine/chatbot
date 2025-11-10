import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# API Keys and LLM Configuration
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Model configuration
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")  # ou gemini-1.5-flash pour Gemini
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))


def get_system_prompt():
    """
    Génère le prompt système avec la date et l'heure actuelles (UTC).
    
    Returns:
        str: Le prompt système avec contexte temporel
    """
    now_utc = datetime.utcnow()
    date_str = now_utc.strftime("%A %d %B %Y")  # Ex: Friday 08 November 2025
    time_str = now_utc.strftime("%H:%M UTC")    # Ex: 14:30 UTC
    
    # Traduction des jours et mois en français
    jours = {
        'Monday': 'Lundi', 'Tuesday': 'Mardi', 'Wednesday': 'Mercredi',
        'Thursday': 'Jeudi', 'Friday': 'Vendredi', 'Saturday': 'Samedi', 'Sunday': 'Dimanche'
    }
    mois = {
        'January': 'janvier', 'February': 'février', 'March': 'mars', 'April': 'avril',
        'May': 'mai', 'June': 'juin', 'July': 'juillet', 'August': 'août',
        'September': 'septembre', 'October': 'octobre', 'November': 'novembre', 'December': 'décembre'
    }
    
    for eng, fr in jours.items():
        date_str = date_str.replace(eng, fr)
    for eng, fr in mois.items():
        date_str = date_str.replace(eng, fr)
    
    return f"""Tu es un assistant intelligent pour Conso News, une plateforme d'actualités et de consommation.

CONTEXTE TEMPOREL:
Nous sommes le {date_str}, il est {time_str}.
Utilise cette information pour contextualiser tes réponses et recherches.

Ton rôle est d'aider les utilisateurs en:
1. Répondant aux questions sur l'actualité et les nouvelles
2. Recherchant des informations en ligne quand nécessaire
3. Fournissant des informations sur les marques et produits
4. Aidant à comparer des offres et des prix

Tu dois TOUJOURS répondre en français de manière claire, professionnelle et utile.

Quand tu utilises la recherche web:
- Cite tes sources
- Résume les informations de manière concise
- Indique la date des informations quand c'est pertinent
- Tiens compte du contexte temporel actuel

Reste factuel et objectif dans tes réponses."""


# Compatibilité: garder SYSTEM_PROMPT comme variable pour le code existant
SYSTEM_PROMPT = get_system_prompt()
