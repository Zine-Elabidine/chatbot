from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from agent import ConsoNewsAgent
from session_manager import session_manager
from langchain_core.messages import HumanMessage, AIMessage
from apscheduler.schedulers.background import BackgroundScheduler
from news_store import index_new_posts
import uvicorn
import os

# Initialisation de l'application FastAPI
app = FastAPI(
    title="Conso News Chatbot API",
    description="API pour le chatbot intelligent de Conso News avec recherche web",
    version="1.0.0"
)

# Configuration CORS pour permettre les requêtes depuis WordPress
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    """Démarre le planificateur pour l'indexation incrémentale des nouveaux articles."""
    # Start scheduler first so port opens quickly
    scheduler.start()
    
    # Check for new posts on startup (last 14 hours to catch any missed)
    print("📰 Scheduling startup indexing (last 14 hours)...")
    scheduler.add_job(
        index_new_posts, 
        "date",  # Run once immediately
        kwargs={"hours": 14}
    )
    
    # Tâche récurrente toutes les 12 heures pour indexer les nouveaux articles
    # Fetch 14h window to have 2h overlap buffer
    scheduler.add_job(
        index_new_posts, 
        "interval", 
        hours=12, 
        kwargs={"hours": 14}
    )
    print("✅ Scheduler started: indexing every 12h (14h window)")


@app.on_event("shutdown")
def shutdown_event():
    """Arrête proprement le planificateur."""
    if scheduler.running:
        scheduler.shutdown()

# Initialisation de l'agent
agent = ConsoNewsAgent()

# Planificateur pour la synchronisation des articles WordPress
scheduler = BackgroundScheduler()

# Modèles Pydantic pour les requêtes/réponses
class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    chat_history: Optional[List[ChatMessage]] = None


class SessionChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    success: bool = True


class SessionChatResponse(BaseModel):
    response: str
    session_id: str
    message_count: int
    success: bool = True


class SessionResponse(BaseModel):
    session_id: str
    message: str


class HealthResponse(BaseModel):
    status: str
    message: str


@app.get("/api/health", response_model=HealthResponse)
async def root():
    """Endpoint racine."""
    return {
        "status": "online",
        "message": "Bienvenue sur l'API du chatbot Conso News!"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Vérification de l'état de santé de l'API."""
    return {
        "status": "healthy",
        "message": "Le service est opérationnel"
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint principal pour interagir avec le chatbot.
    
    Args:
        request: ChatRequest contenant le message et l'historique optionnel
    
    Returns:
        ChatResponse avec la réponse du chatbot
    """
    try:
        # Convertir l'historique si présent
        chat_history = None
        if request.chat_history:
            from langchain_core.messages import HumanMessage, AIMessage
            chat_history = []
            for msg in request.chat_history:
                if msg.role == "user":
                    chat_history.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    chat_history.append(AIMessage(content=msg.content))
        
        # Obtenir la réponse de l'agent
        result = await agent.achat(request.message, chat_history)
        
        return ChatResponse(
            response=result["response"],
            success=True
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du traitement de la requête: {str(e)}"
        )


@app.post("/chat/simple")
async def chat_simple(request: ChatRequest):
    """
    Endpoint simplifié sans historique pour des requêtes rapides.
    
    Args:
        request: ChatRequest avec juste le message
    
    Returns:
        Réponse simple en texte
    """
    try:
        result = await agent.achat(request.message)
        return {"response": result["response"]}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur: {str(e)}"
        )


# ===== ENDPOINTS AVEC GESTION DE SESSIONS =====

@app.post("/session/new", response_model=SessionResponse)
async def create_session():
    """
    Crée une nouvelle session de chat.
    
    Returns:
        SessionResponse avec le session_id
    """
    session_id = session_manager.create_session()
    return {
        "session_id": session_id,
        "message": "Session créée avec succès"
    }


@app.post("/session/chat", response_model=SessionChatResponse)
async def chat_with_session(request: SessionChatRequest):
    """
    Chat avec gestion automatique de l'historique via session.
    
    Args:
        request: SessionChatRequest avec message et session_id optionnel
    
    Returns:
        SessionChatResponse avec la réponse et le session_id
    """
    try:
        # Créer une nouvelle session si aucune n'est fournie
        session_id = request.session_id
        if not session_id:
            session_id = session_manager.create_session()
        
        # Récupérer l'historique de la session
        chat_history = session_manager.get_messages(session_id)
        if chat_history is None:
            # Session expirée ou inexistante, créer une nouvelle
            session_id = session_manager.create_session()
            chat_history = []
        
        # Ajouter le message utilisateur
        user_message = HumanMessage(content=request.message)
        session_manager.add_message(session_id, user_message)
        
        # Obtenir la réponse de l'agent avec l'historique
        result = await agent.achat(request.message, chat_history)
        
        # Ajouter la réponse de l'assistant à l'historique
        assistant_message = AIMessage(content=result["response"])
        session_manager.add_message(session_id, assistant_message)
        
        # Récupérer le nombre de messages
        session_info = session_manager.get_session_info(session_id)
        message_count = session_info["message_count"] if session_info else 0
        
        return SessionChatResponse(
            response=result["response"],
            session_id=session_id,
            message_count=message_count,
            success=True
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du traitement de la requête: {str(e)}"
        )


@app.get("/session/{session_id}/info")
async def get_session_info(session_id: str):
    """
    Récupère les informations d'une session.
    
    Args:
        session_id: ID de la session
    
    Returns:
        Informations de la session
    """
    info = session_manager.get_session_info(session_id)
    if info is None:
        raise HTTPException(
            status_code=404,
            detail="Session non trouvée ou expirée"
        )
    return info


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    Supprime une session.
    
    Args:
        session_id: ID de la session
    
    Returns:
        Message de confirmation
    """
    success = session_manager.clear_session(session_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Session non trouvée"
        )
    return {"message": "Session supprimée avec succès"}


@app.get("/sessions/stats")
async def get_sessions_stats():
    """
    Récupère les statistiques des sessions actives.
    
    Returns:
        Nombre de sessions actives
    """
    return {
        "active_sessions": session_manager.get_all_sessions_count()
    }


# Servir le fichier HTML à la racine
@app.get("/")
async def serve_frontend():
    """Servir l'interface frontend."""
    return FileResponse("index.html")


if __name__ == "__main__":
    # Lancer le serveur
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
