/**
 * Exemple d'intégration WordPress pour le chatbot Conso News
 * À ajouter dans un plugin WordPress ou via Custom HTML/JavaScript
 * 
 * Utilise le système de sessions pour maintenir l'historique
 */

(function() {
    'use strict';
    
    // Configuration
    const CONFIG = {
        API_URL: 'http://localhost:8000',
        SESSION_STORAGE_KEY: 'conso_news_chatbot_session'
    };
    
    let sessionId = null;
    
    /**
     * Classe principale du chatbot
     */
    class ConsoNewsChatbot {
        constructor(config) {
            this.apiUrl = config.API_URL;
            this.storageKey = config.SESSION_STORAGE_KEY;
            this.sessionId = null;
            this.isOpen = false;
            
            this.init();
        }
        
        /**
         * Initialisation du chatbot
         */
        async init() {
            await this.loadMarkdownLibrary();
            this.createChatWidget();
            await this.initSession();
            this.attachEventListeners();
        }
        
        /**
         * Charger la bibliothèque Marked.js pour le rendu markdown
         */
        async loadMarkdownLibrary() {
            return new Promise((resolve, reject) => {
                // Vérifier si marked est déjà chargé
                if (window.marked) {
                    resolve();
                    return;
                }
                
                const script = document.createElement('script');
                script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
                script.onload = () => resolve();
                script.onerror = () => {
                    console.warn('[Chatbot] Marked.js non chargé, fallback vers texte brut');
                    resolve();
                };
                document.head.appendChild(script);
            });
        }
        
        /**
         * Créer le widget HTML du chatbot
         */
        createChatWidget() {
            const widgetHTML = `
                <div id="conso-chatbot-widget" class="conso-chatbot-closed">
                    <!-- Bouton flottant -->
                    <div id="conso-chatbot-button" class="conso-chatbot-fab">
                        💬
                    </div>
                    
                    <!-- Fenêtre de chat -->
                    <div id="conso-chatbot-window" class="conso-chatbot-window">
                        <div class="conso-chatbot-header">
                            <div class="conso-chatbot-header-title">
                                <strong>🤖 Conso News Assistant</strong>
                                <span class="conso-chatbot-status">En ligne</span>
                            </div>
                            <div class="conso-chatbot-header-actions">
                                <button id="conso-chatbot-reset" class="conso-chatbot-reset-btn" title="Nouvelle conversation">🔄</button>
                                <button id="conso-chatbot-close" class="conso-chatbot-close-btn">✕</button>
                            </div>
                        </div>
                        
                        <div id="conso-chatbot-messages" class="conso-chatbot-messages">
                            <div class="conso-chatbot-message assistant">
                                <div class="conso-chatbot-message-content">
                                    👋 Bonjour! Je suis l'assistant Conso News. Comment puis-je vous aider?
                                </div>
                            </div>
                        </div>
                        
                        <div class="conso-chatbot-input-container">
                            <input 
                                type="text" 
                                id="conso-chatbot-input" 
                                placeholder="Posez votre question..."
                                autocomplete="off"
                            />
                            <button id="conso-chatbot-send">Envoyer</button>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.insertAdjacentHTML('beforeend', widgetHTML);
            this.injectStyles();
        }
        
        /**
         * Injecter les styles CSS
         */
        injectStyles() {
            const styles = `
                <style>
                    #conso-chatbot-widget {
                        position: fixed;
                        bottom: 24px;
                        right: 24px;
                        z-index: 9999;
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    }

                    .conso-chatbot-fab {
                        width: 64px;
                        height: 64px;
                        border-radius: 9999px;
                        background: linear-gradient(135deg, #d90429 0%, #ff4b4b 100%);
                        color: #ffffff;
                        font-size: 28px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        cursor: pointer;
                        box-shadow: 0 10px 25px rgba(0,0,0,0.35);
                        transition: transform 0.2s, box-shadow 0.2s;
                    }

                    .conso-chatbot-fab:hover {
                        transform: scale(1.05) translateY(-1px);
                        box-shadow: 0 14px 35px rgba(0,0,0,0.45);
                    }

                    .conso-chatbot-window {
                        display: none;
                        position: fixed;
                        bottom: 100px;
                        right: 24px;
                        width: min(480px, 95vw);
                        height: min(70vh, 640px);
                        background: #111827;
                        border-radius: 16px;
                        box-shadow: 0 18px 45px rgba(0,0,0,0.4);
                        flex-direction: column;
                        overflow: hidden;
                        border: 1px solid rgba(0,0,0,0.6);
                    }

                    #conso-chatbot-widget:not(.conso-chatbot-closed) .conso-chatbot-window {
                        display: flex;
                    }

                    .conso-chatbot-header {
                        background: linear-gradient(135deg, #111827 0%, #000000 40%, #d90429 100%);
                        color: #ffffff;
                        padding: 14px 16px;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        border-bottom: 1px solid rgba(255,255,255,0.08);
                    }

                    .conso-chatbot-header-title strong {
                        display: block;
                        font-size: 15px;
                        letter-spacing: 0.02em;
                    }

                    .conso-chatbot-status {
                        font-size: 11px;
                        opacity: 0.9;
                        color: #f9fafb;
                    }

                    .conso-chatbot-header-actions {
                        display: flex;
                        gap: 8px;
                        align-items: center;
                    }

                    .conso-chatbot-reset-btn,
                    .conso-chatbot-close-btn {
                        background: transparent;
                        border: none;
                        color: #f9fafb;
                        font-size: 18px;
                        cursor: pointer;
                        padding: 0;
                        width: 28px;
                        height: 28px;
                        border-radius: 9999px;
                        transition: background-color 0.15s, transform 0.15s, opacity 0.15s;
                    }

                    .conso-chatbot-reset-btn:hover,
                    .conso-chatbot-close-btn:hover {
                        opacity: 0.9;
                        background-color: rgba(248,113,113,0.18);
                        transform: scale(1.05);
                    }

                    .conso-chatbot-close-btn {
                        font-size: 20px;
                    }

                    .conso-chatbot-messages {
                        flex: 1;
                        overflow-y: auto;
                        padding: 14px 14px 10px;
                        background: #f9fafb;
                    }

                    .conso-chatbot-message {
                        margin-bottom: 10px;
                        display: flex;
                        animation: fadeIn 0.25s ease-out;
                    }

                    @keyframes fadeIn {
                        from { opacity: 0; transform: translateY(8px); }
                        to { opacity: 1; transform: translateY(0); }
                    }

                    .conso-chatbot-message.user {
                        justify-content: flex-end;
                    }

                    .conso-chatbot-message-content {
                        max-width: 78%;
                        padding: 10px 12px;
                        border-radius: 16px;
                        word-wrap: break-word;
                        font-size: 14px;
                        line-height: 1.5;
                    }

                    .conso-chatbot-message.assistant .conso-chatbot-message-content {
                        background: #ffffff;
                        border: 1px solid #e5e7eb;
                        color: #111827;
                    }

                    .conso-chatbot-message.user .conso-chatbot-message-content {
                        background: linear-gradient(135deg, #d90429 0%, #ff4b4b 100%);
                        color: #ffffff;
                        border: none;
                    }

                    /* Styles pour le contenu markdown */
                    .conso-chatbot-message-content h1,
                    .conso-chatbot-message-content h2,
                    .conso-chatbot-message-content h3 {
                        margin-top: 6px;
                        margin-bottom: 4px;
                        font-weight: 600;
                    }

                    .conso-chatbot-message-content h1 { font-size: 18px; }
                    .conso-chatbot-message-content h2 { font-size: 16px; }
                    .conso-chatbot-message-content h3 { font-size: 15px; }

                    .conso-chatbot-message-content p {
                        margin-bottom: 6px;
                        line-height: 1.6;
                        font-size: 14px;
                    }

                    .conso-chatbot-message-content ul,
                    .conso-chatbot-message-content ol {
                        margin-left: 18px;
                        margin-bottom: 4px;
                    }

                    .conso-chatbot-message-content li {
                        margin-bottom: 2px;
                        line-height: 1.4;
                    }

                    .conso-chatbot-message-content code {
                        background: #f3f4f6;
                        padding: 2px 5px;
                        border-radius: 4px;
                        font-family: 'Courier New', monospace;
                        font-size: 13px;
                    }

                    .conso-chatbot-message-content pre {
                        background: #111827;
                        color: #e5e7eb;
                        padding: 8px;
                        border-radius: 6px;
                        overflow-x: auto;
                        margin-bottom: 6px;
                        font-size: 13px;
                    }

                    .conso-chatbot-message-content pre code {
                        background: none;
                        padding: 0;
                    }

                    .conso-chatbot-message-content blockquote {
                        border-left: 3px solid #d90429;
                        padding-left: 10px;
                        margin: 6px 0;
                        color: #4b5563;
                        font-style: italic;
                    }

                    /* Tables markdown */
                    .conso-chatbot-message-content table {
                        width: 100%;
                        border-collapse: collapse;
                        margin: 8px 0;
                        font-size: 13px;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
                    }

                    .conso-chatbot-message-content table thead {
                        background: #111827;
                        color: #f9fafb;
                    }

                    .conso-chatbot-message-content table th {
                        padding: 8px;
                        text-align: left;
                        font-weight: 600;
                        border: 1px solid #e5e7eb;
                    }

                    .conso-chatbot-message-content table td {
                        padding: 6px 8px;
                        border: 1px solid #e5e7eb;
                    }

                    .conso-chatbot-message-content table tbody tr:nth-child(even) {
                        background-color: #f9fafb;
                    }

                    .conso-chatbot-message-content table tbody tr:hover {
                        background-color: #f3f4f6;
                    }

                    .conso-chatbot-message-content a {
                        color: #b91c1c;
                        text-decoration: underline;
                    }

                    .conso-chatbot-message-content a:hover {
                        color: #ef4444;
                    }

                    .conso-chatbot-message-content strong {
                        font-weight: 600;
                    }

                    .conso-chatbot-message-content em {
                        font-style: italic;
                    }

                    .conso-chatbot-message-content hr {
                        border: none;
                        border-top: 1px solid #e5e7eb;
                        margin: 8px 0;
                    }

                    .conso-chatbot-input-container {
                        padding: 12px 14px;
                        background: #111827;
                        border-top: 1px solid rgba(255,255,255,0.06);
                        display: flex;
                        gap: 8px;
                        align-items: center;
                    }

                    .conso-chatbot-typing {
                        display: inline-block;
                        padding: 8px 12px;
                        background: #ffffff;
                        border: 1px solid #e5e7eb;
                        border-radius: 9999px;
                    }

                    .conso-chatbot-typing span {
                        height: 6px;
                        width: 6px;
                        background: #d90429;
                        border-radius: 50%;
                        display: inline-block;
                        margin-right: 4px;
                        animation: typing 1.4s infinite;
                    }

                    .conso-chatbot-typing span:nth-child(2) { animation-delay: 0.2s; }
                    .conso-chatbot-typing span:nth-child(3) { animation-delay: 0.4s; }

                    @keyframes typing {
                        0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
                        30% { transform: translateY(-6px); opacity: 1; }
                    }

                    #conso-chatbot-input {
                        flex: 1;
                        padding: 10px 14px;
                        border: 1px solid #374151;
                        border-radius: 9999px;
                        font-size: 14px;
                        outline: none;
                        background: #111827;
                        color: #f9fafb;
                    }

                    #conso-chatbot-input::placeholder {
                        color: #6b7280;
                    }

                    #conso-chatbot-input:focus {
                        border-color: #f87171;
                        box-shadow: 0 0 0 1px rgba(248,113,113,0.7);
                    }

                    #conso-chatbot-send {
                        padding: 9px 18px;
                        background: linear-gradient(135deg, #d90429 0%, #ff4b4b 100%);
                        color: #ffffff;
                        border: none;
                        border-radius: 9999px;
                        font-size: 14px;
                        font-weight: 600;
                        cursor: pointer;
                        transition: transform 0.2s, box-shadow 0.2s, background 0.2s;
                        white-space: nowrap;
                    }

                    #conso-chatbot-send:hover {
                        transform: translateY(-1px);
                        box-shadow: 0 8px 20px rgba(0,0,0,0.4);
                        background: linear-gradient(135deg, #b91c1c 0%, #ef4444 100%);
                    }

                    @media (max-width: 480px) {
                        .conso-chatbot-window {
                            right: 12px;
                            bottom: 88px;
                            width: calc(100vw - 24px);
                            height: min(75vh, 620px);
                        }
                    }
                </style>
            `;

            document.head.insertAdjacentHTML('beforeend', styles);
        }
        
        /**
         * Initialiser ou récupérer une session
         */
        async initSession() {
            // Vérifier localStorage
            const savedSessionId = localStorage.getItem(this.storageKey);
            
            if (savedSessionId) {
                // Vérifier si la session est valide
                try {
                    const response = await fetch(`${this.apiUrl}/session/${savedSessionId}/info`);
                    if (response.ok) {
                        this.sessionId = savedSessionId;
                        console.log('[Chatbot] Session existante chargée');
                        return;
                    }
                } catch (error) {
                    console.log('[Chatbot] Session expirée');
                }
            }
            
            // Créer une nouvelle session
            try {
                const response = await fetch(`${this.apiUrl}/session/new`, {
                    method: 'POST'
                });
                const data = await response.json();
                this.sessionId = data.session_id;
                localStorage.setItem(this.storageKey, this.sessionId);
                console.log('[Chatbot] Nouvelle session créée');
            } catch (error) {
                console.error('[Chatbot] Erreur création session:', error);
            }
        }
        
        /**
         * Attacher les event listeners
         */
        attachEventListeners() {
            const button = document.getElementById('conso-chatbot-button');
            const closeBtn = document.getElementById('conso-chatbot-close');
            const resetBtn = document.getElementById('conso-chatbot-reset');
            const sendBtn = document.getElementById('conso-chatbot-send');
            const input = document.getElementById('conso-chatbot-input');
            
            button.addEventListener('click', () => this.toggleChat());
            closeBtn.addEventListener('click', () => this.toggleChat());
            resetBtn.addEventListener('click', () => this.resetConversation());
            sendBtn.addEventListener('click', () => this.sendMessage());
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.sendMessage();
            });
        }
        
        /**
         * Basculer l'affichage du chat
         */
        toggleChat() {
            const widget = document.getElementById('conso-chatbot-widget');
            widget.classList.toggle('conso-chatbot-closed');
            this.isOpen = !this.isOpen;
            
            if (this.isOpen) {
                document.getElementById('conso-chatbot-input').focus();
            }
        }
        
        /**
         * Ajouter un message à l'affichage
         */
        addMessage(role, content) {
            const messagesContainer = document.getElementById('conso-chatbot-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `conso-chatbot-message ${role}`;
            
            // Parser le markdown pour les messages de l'assistant
            let htmlContent;
            if (role === 'assistant' && window.marked) {
                // Configurer marked
                window.marked.setOptions({
                    breaks: true,
                    gfm: true,
                });
                htmlContent = window.marked.parse(content);
            } else {
                // Texte brut pour les utilisateurs ou fallback
                htmlContent = this.escapeHtml(content);
            }
            
            messageDiv.innerHTML = `
                <div class="conso-chatbot-message-content">${htmlContent}</div>
            `;
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        /**
         * Afficher l'indicateur de saisie
         */
        showTyping() {
            const messagesContainer = document.getElementById('conso-chatbot-messages');
            const typingDiv = document.createElement('div');
            typingDiv.id = 'conso-chatbot-typing';
            typingDiv.className = 'conso-chatbot-message assistant';
            typingDiv.innerHTML = `
                <div class="conso-chatbot-typing">
                    <span></span><span></span><span></span>
                </div>
            `;
            messagesContainer.appendChild(typingDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        /**
         * Masquer l'indicateur de saisie
         */
        hideTyping() {
            const typing = document.getElementById('conso-chatbot-typing');
            if (typing) typing.remove();
        }
        
        /**
         * Envoyer un message
         */
        async sendMessage() {
            const input = document.getElementById('conso-chatbot-input');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Afficher le message utilisateur
            this.addMessage('user', message);
            input.value = '';
            input.disabled = true;
            
            // Afficher typing indicator
            this.showTyping();
            
            try {
                const response = await fetch(`${this.apiUrl}/session/chat`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        message: message,
                        session_id: this.sessionId
                    })
                });
                
                this.hideTyping();
                
                if (!response.ok) {
                    throw new Error('Erreur réseau');
                }
                
                const data = await response.json();
                
                // Mettre à jour session_id si nécessaire
                if (data.session_id !== this.sessionId) {
                    this.sessionId = data.session_id;
                    localStorage.setItem(this.storageKey, this.sessionId);
                }
                
                // Afficher la réponse
                this.addMessage('assistant', data.response);
                
            } catch (error) {
                this.hideTyping();
                console.error('[Chatbot] Erreur:', error);
                this.addMessage('assistant', '❌ Désolé, une erreur est survenue. Veuillez réessayer.');
            } finally {
                input.disabled = false;
                input.focus();
            }
        }
        
        /**
         * Réinitialiser la conversation
         */
        async resetConversation() {
            if (!confirm('Voulez-vous vraiment recommencer une nouvelle conversation?')) {
                return;
            }
            
            // Supprimer la session actuelle
            if (this.sessionId) {
                try {
                    await fetch(`${this.apiUrl}/session/${this.sessionId}`, {
                        method: 'DELETE'
                    });
                    console.log('[Chatbot] Session supprimée');
                } catch (error) {
                    console.error('[Chatbot] Erreur suppression:', error);
                }
            }
            
            // Nettoyer localStorage et session
            localStorage.removeItem(this.storageKey);
            this.sessionId = null;
            
            // Vider l'affichage des messages
            const messagesContainer = document.getElementById('conso-chatbot-messages');
            messagesContainer.innerHTML = `
                <div class="conso-chatbot-message assistant">
                    <div class="conso-chatbot-message-content">
                        👋 Bonjour! Je suis l'assistant Conso News. Comment puis-je vous aider?
                    </div>
                </div>
            `;
            
            // Créer une nouvelle session
            await this.initSession();
            
            console.log('[Chatbot] Nouvelle conversation démarrée');
            document.getElementById('conso-chatbot-input').focus();
        }
        
        /**
         * Échapper le HTML
         */
        escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    }
    
    // Initialiser le chatbot au chargement de la page
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.consoNewsChatbot = new ConsoNewsChatbot(CONFIG);
        });
    } else {
        window.consoNewsChatbot = new ConsoNewsChatbot(CONFIG);
    }
    
})();
