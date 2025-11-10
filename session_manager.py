"""
Gestionnaire de sessions pour l'historique des conversations.
Système simple en mémoire avec expiration automatique (TTL).
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import threading
import time


class SessionManager:
    """Gestionnaire de sessions avec historique temporaire en mémoire."""
    
    def __init__(self, session_timeout_minutes: int = 30):
        """
        Initialise le gestionnaire de sessions.
        
        Args:
            session_timeout_minutes: Durée d'expiration des sessions en minutes
        """
        self.sessions: Dict[str, Dict] = {}
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.lock = threading.Lock()
        
        # Démarrer le nettoyage automatique des sessions expirées
        self._start_cleanup_thread()
    
    def create_session(self) -> str:
        """
        Crée une nouvelle session et retourne son ID.
        
        Returns:
            session_id: Identifiant unique de la session
        """
        session_id = str(uuid.uuid4())
        
        with self.lock:
            self.sessions[session_id] = {
                "messages": [],
                "created_at": datetime.now(),
                "last_activity": datetime.now()
            }
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Récupère une session par son ID.
        
        Args:
            session_id: ID de la session
            
        Returns:
            Session dict ou None si expirée/inexistante
        """
        with self.lock:
            if session_id not in self.sessions:
                return None
            
            session = self.sessions[session_id]
            
            # Vérifier si la session a expiré
            if datetime.now() - session["last_activity"] > self.session_timeout:
                del self.sessions[session_id]
                return None
            
            # Mettre à jour le timestamp d'activité
            session["last_activity"] = datetime.now()
            return session
    
    def get_messages(self, session_id: str) -> Optional[List[BaseMessage]]:
        """
        Récupère l'historique des messages d'une session.
        
        Args:
            session_id: ID de la session
            
        Returns:
            Liste des messages ou None si session inexistante
        """
        session = self.get_session(session_id)
        if session is None:
            return None
        return session["messages"]
    
    def add_message(self, session_id: str, message: BaseMessage) -> bool:
        """
        Ajoute un message à l'historique de la session.
        
        Args:
            session_id: ID de la session
            message: Message à ajouter
            
        Returns:
            True si succès, False si session inexistante
        """
        session = self.get_session(session_id)
        if session is None:
            return False
        
        with self.lock:
            session["messages"].append(message)
            session["last_activity"] = datetime.now()
        
        return True
    
    def add_messages(self, session_id: str, messages: List[BaseMessage]) -> bool:
        """
        Ajoute plusieurs messages à l'historique de la session.
        
        Args:
            session_id: ID de la session
            messages: Liste de messages à ajouter
            
        Returns:
            True si succès, False si session inexistante
        """
        session = self.get_session(session_id)
        if session is None:
            return False
        
        with self.lock:
            session["messages"].extend(messages)
            session["last_activity"] = datetime.now()
        
        return True
    
    def clear_session(self, session_id: str) -> bool:
        """
        Efface une session.
        
        Args:
            session_id: ID de la session
            
        Returns:
            True si succès, False si session inexistante
        """
        with self.lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                return True
            return False
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """
        Récupère les informations d'une session.
        
        Args:
            session_id: ID de la session
            
        Returns:
            Dict avec infos de la session ou None
        """
        session = self.get_session(session_id)
        if session is None:
            return None
        
        return {
            "session_id": session_id,
            "message_count": len(session["messages"]),
            "created_at": session["created_at"].isoformat(),
            "last_activity": session["last_activity"].isoformat(),
            "expires_in_minutes": int(
                (self.session_timeout - (datetime.now() - session["last_activity"])).total_seconds() / 60
            )
        }
    
    def get_all_sessions_count(self) -> int:
        """Retourne le nombre de sessions actives."""
        with self.lock:
            return len(self.sessions)
    
    def _cleanup_expired_sessions(self):
        """Nettoie les sessions expirées (exécuté périodiquement)."""
        while True:
            time.sleep(300)  # Vérifier toutes les 5 minutes
            
            with self.lock:
                now = datetime.now()
                expired_sessions = [
                    session_id for session_id, session in self.sessions.items()
                    if now - session["last_activity"] > self.session_timeout
                ]
                
                for session_id in expired_sessions:
                    del self.sessions[session_id]
                
                if expired_sessions:
                    print(f"🧹 Nettoyage: {len(expired_sessions)} sessions expirées supprimées")
    
    def _start_cleanup_thread(self):
        """Démarre le thread de nettoyage automatique."""
        cleanup_thread = threading.Thread(
            target=self._cleanup_expired_sessions,
            daemon=True
        )
        cleanup_thread.start()


# Instance globale du gestionnaire de sessions
session_manager = SessionManager(session_timeout_minutes=30)
