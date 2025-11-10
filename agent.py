from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from config import LLM_API_KEY, LLM_BASE_URL, TAVILY_API_KEY, MODEL_NAME, TEMPERATURE, get_system_prompt


class AgentState(TypedDict):
    """État de l'agent avec historique des messages."""
    messages: Annotated[Sequence[BaseMessage], add_messages]


class ConsoNewsAgent:
    """Agent LangGraph pour Conso News avec capacités de recherche web."""
    
    def __init__(self):
        # Initialisation du modèle (compatible OpenAI)
        self.llm = ChatOpenAI(
            model=MODEL_NAME,
            temperature=TEMPERATURE,
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL
        )
        
        # Initialisation de l'outil de recherche web Tavily
        self.search_tool = TavilySearchResults(
            max_results=5,
            search_depth="advanced",
            api_key=TAVILY_API_KEY,
            description="""Outil de recherche web pour trouver des informations actualisées sur internet.
            Utilise cet outil pour:
            - Rechercher des actualités récentes
            - Trouver des informations sur des marques et produits
            - Comparer des prix et des offres
            - Obtenir des informations à jour sur n'importe quel sujet"""
        )
        
        # Liste des outils disponibles
        self.tools = [self.search_tool]
        
        # LLM avec outils bindés
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Construction du graph
        self.graph = self._build_graph()
    
    def _should_continue(self, state: AgentState):
        """Détermine si l'agent doit continuer ou terminer."""
        messages = state["messages"]
        last_message = messages[-1]
        
        # Si le dernier message a des tool_calls, on continue
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        # Sinon, on termine
        return END
    
    def _call_model(self, state: AgentState):
        """Appelle le modèle avec le contexte système (avec date/heure UTC actuelle)."""
        messages = state["messages"]
        
        # Ajouter le prompt système au début si ce n'est pas déjà fait
        # Utilise get_system_prompt() pour avoir la date/heure actuelle
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=get_system_prompt())] + list(messages)
        
        response = self.llm_with_tools.invoke(messages)
        return {"messages": [response]}
    
    def _build_graph(self):
        """Construit le graph LangGraph."""
        workflow = StateGraph(AgentState)
        
        # Définir les noeuds
        workflow.add_node("agent", self._call_model)
        workflow.add_node("tools", ToolNode(self.tools))
        
        # Définir le point d'entrée
        workflow.set_entry_point("agent")
        
        # Définir les edges conditionnels
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "tools": "tools",
                END: END
            }
        )
        
        # Après les outils, retourner à l'agent
        workflow.add_edge("tools", "agent")
        
        return workflow.compile()
    
    def chat(self, message: str, chat_history: list = None):
        """
        Fonction principale pour interagir avec l'agent.
        
        Args:
            message: Le message de l'utilisateur
            chat_history: Historique optionnel des messages
        
        Returns:
            La réponse de l'agent et l'historique mis à jour
        """
        # Préparer les messages
        if chat_history is None:
            messages = [HumanMessage(content=message)]
        else:
            messages = chat_history + [HumanMessage(content=message)]
        
        # Exécuter le graph
        result = self.graph.invoke({"messages": messages})
        
        # Extraire la réponse
        response_message = result["messages"][-1]
        response_content = response_message.content
        
        return {
            "response": response_content,
            "chat_history": result["messages"]
        }
    
    async def achat(self, message: str, chat_history: list = None):
        """Version asynchrone de la fonction chat."""
        # Préparer les messages
        if chat_history is None:
            messages = [HumanMessage(content=message)]
        else:
            messages = chat_history + [HumanMessage(content=message)]
        
        # Exécuter le graph de manière asynchrone
        result = await self.graph.ainvoke({"messages": messages})
        
        # Extraire la réponse
        response_message = result["messages"][-1]
        response_content = response_message.content
        
        return {
            "response": response_content,
            "chat_history": result["messages"]
        }
