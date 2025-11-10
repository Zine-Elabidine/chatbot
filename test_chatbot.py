"""
Script de test pour le chatbot Conso News.
Lance quelques requêtes d'exemple pour vérifier que tout fonctionne.
"""

import requests
import json
from time import sleep

API_URL = "http://localhost:8000"

def test_health():
    """Test du endpoint de santé."""
    print("\n🔍 Test du endpoint /health...")
    response = requests.get(f"{API_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_simple_chat():
    """Test d'une requête simple."""
    print("\n💬 Test d'une question simple...")
    
    payload = {
        "message": "Bonjour! Peux-tu te présenter?"
    }
    
    response = requests.post(
        f"{API_URL}/chat/simple",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Réponse du chatbot:\n{result['response']}")
        return True
    else:
        print(f"Erreur: {response.text}")
        return False

def test_web_search():
    """Test avec recherche web."""
    print("\n🌐 Test avec recherche web...")
    
    payload = {
        "message": "Quelles sont les dernières actualités sur l'intelligence artificielle?"
    }
    
    response = requests.post(
        f"{API_URL}/chat/simple",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Réponse du chatbot:\n{result['response']}")
        return True
    else:
        print(f"Erreur: {response.text}")
        return False

def test_price_comparison():
    """Test de comparaison de prix."""
    print("\n💰 Test de comparaison de prix...")
    
    payload = {
        "message": "Compare les prix des smartphones Samsung Galaxy S24 actuellement disponibles"
    }
    
    response = requests.post(
        f"{API_URL}/chat/simple",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Réponse du chatbot:\n{result['response']}")
        return True
    else:
        print(f"Erreur: {response.text}")
        return False

def test_conversation_history():
    """Test avec historique de conversation."""
    print("\n💭 Test avec historique de conversation...")
    
    # Première question
    payload1 = {
        "message": "Parle-moi des ordinateurs portables pour le gaming"
    }
    
    response1 = requests.post(f"{API_URL}/chat", json=payload1)
    if response1.status_code != 200:
        print(f"Erreur première requête: {response1.text}")
        return False
    
    result1 = response1.json()
    print(f"Question 1: {payload1['message']}")
    print(f"Réponse 1: {result1['response'][:200]}...\n")
    
    # Deuxième question avec contexte
    payload2 = {
        "message": "Quels sont les meilleurs modèles sous 1000€?",
        "chat_history": [
            {"role": "user", "content": payload1['message']},
            {"role": "assistant", "content": result1['response']}
        ]
    }
    
    response2 = requests.post(f"{API_URL}/chat", json=payload2)
    if response2.status_code != 200:
        print(f"Erreur deuxième requête: {response2.text}")
        return False
    
    result2 = response2.json()
    print(f"Question 2 (avec contexte): {payload2['message']}")
    print(f"Réponse 2: {result2['response']}")
    
    return True

def main():
    """Fonction principale pour lancer tous les tests."""
    print("=" * 60)
    print("🤖 TESTS DU CHATBOT CONSO NEWS")
    print("=" * 60)
    
    # Vérifier que le serveur est en ligne
    try:
        if not test_health():
            print("\n❌ Le serveur n'est pas accessible. Assurez-vous qu'il est lancé avec 'python main.py'")
            return
    except requests.exceptions.ConnectionError:
        print("\n❌ Impossible de se connecter au serveur.")
        print("Assurez-vous que le serveur est lancé avec 'python main.py'")
        return
    
    print("\n✅ Le serveur est en ligne!")
    
    # Lancer les tests
    tests = [
        ("Question simple", test_simple_chat),
        ("Recherche web", test_web_search),
        ("Comparaison de prix", test_price_comparison),
        ("Historique de conversation", test_conversation_history)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            sleep(2)  # Pause entre les tests
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Erreur lors du test '{test_name}': {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    for test_name, result in results:
        status = "✅ SUCCÈS" if result else "❌ ÉCHEC"
        print(f"{status} - {test_name}")
    
    success_rate = sum(1 for _, r in results if r) / len(results) * 100
    print(f"\nTaux de réussite: {success_rate:.0f}%")
    
    if success_rate == 100:
        print("\n🎉 Tous les tests ont réussi! Le chatbot fonctionne parfaitement.")
    elif success_rate >= 50:
        print("\n⚠️ Certains tests ont échoué. Vérifiez la configuration.")
    else:
        print("\n❌ La plupart des tests ont échoué. Vérifiez les clés API et la configuration.")

if __name__ == "__main__":
    main()
