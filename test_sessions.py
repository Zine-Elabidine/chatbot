"""
Script de test pour le système de sessions du chatbot Conso News.
Test du chat avec historique et gestion des sessions.
"""

import requests
import time

API_URL = "http://localhost:8000"

def test_session_creation():
    """Test de création d'une session."""
    print("\n🔍 Test: Création d'une session")
    response = requests.post(f"{API_URL}/session/new")
    
    if response.status_code == 200:
        data = response.json()
        session_id = data.get("session_id")
        print(f"✅ Session créée: {session_id}")
        return session_id
    else:
        print(f"❌ Erreur: {response.status_code}")
        return None

def test_session_chat(session_id):
    """Test d'un chat avec session."""
    print(f"\n💬 Test: Chat avec historique (session: {session_id[:8]}...)")
    
    questions = [
        "Bonjour! Peux-tu te présenter?",
        "De quoi parlions-nous?",
        "Quel est ton nom?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n📤 Question {i}: {question}")
        
        response = requests.post(
            f"{API_URL}/session/chat",
            json={"message": question, "session_id": session_id}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"📥 Réponse: {data['response'][:150]}...")
            print(f"📊 Messages dans la session: {data['message_count']}")
        else:
            print(f"❌ Erreur: {response.status_code}")
            return False
        
        time.sleep(1)  # Pause entre les questions
    
    return True

def test_session_info(session_id):
    """Test de récupération des informations de session."""
    print(f"\n📊 Test: Informations de la session")
    
    response = requests.get(f"{API_URL}/session/{session_id}/info")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Session ID: {data['session_id']}")
        print(f"✅ Nombre de messages: {data['message_count']}")
        print(f"✅ Créée le: {data['created_at']}")
        print(f"✅ Dernière activité: {data['last_activity']}")
        print(f"✅ Expire dans: {data['expires_in_minutes']} minutes")
        return True
    else:
        print(f"❌ Erreur: {response.status_code}")
        return False

def test_conversation_context():
    """Test du maintien du contexte de conversation."""
    print("\n🔄 Test: Maintien du contexte de conversation")
    
    # Créer une session
    response = requests.post(f"{API_URL}/session/new")
    session_id = response.json()["session_id"]
    
    # Poser une première question
    response1 = requests.post(
        f"{API_URL}/session/chat",
        json={
            "message": "Je m'appelle Jean et je cherche un smartphone",
            "session_id": session_id
        }
    )
    
    if response1.status_code != 200:
        print("❌ Erreur première question")
        return False
    
    print(f"✅ Q1: Je m'appelle Jean et je cherche un smartphone")
    print(f"   R1: {response1.json()['response'][:100]}...")
    
    time.sleep(1)
    
    # Poser une question de suivi qui nécessite le contexte
    response2 = requests.post(
        f"{API_URL}/session/chat",
        json={
            "message": "Quel est mon nom?",
            "session_id": session_id
        }
    )
    
    if response2.status_code != 200:
        print("❌ Erreur deuxième question")
        return False
    
    print(f"✅ Q2: Quel est mon nom?")
    response_text = response2.json()['response']
    print(f"   R2: {response_text[:150]}...")
    
    # Vérifier si le nom est dans la réponse
    if "Jean" in response_text or "jean" in response_text.lower():
        print("✅ Le chatbot se souvient du contexte!")
        return True
    else:
        print("⚠️ Le chatbot ne semble pas se souvenir du contexte")
        return False

def test_session_without_id():
    """Test d'un chat sans fournir de session_id."""
    print("\n🆕 Test: Chat sans session_id (création automatique)")
    
    response = requests.post(
        f"{API_URL}/session/chat",
        json={"message": "Bonjour sans session!"}
    )
    
    if response.status_code == 200:
        data = response.json()
        session_id = data.get("session_id")
        print(f"✅ Session créée automatiquement: {session_id}")
        print(f"✅ Réponse: {data['response'][:100]}...")
        return True
    else:
        print(f"❌ Erreur: {response.status_code}")
        return False

def test_session_deletion(session_id):
    """Test de suppression d'une session."""
    print(f"\n🗑️ Test: Suppression de session")
    
    response = requests.delete(f"{API_URL}/session/{session_id}")
    
    if response.status_code == 200:
        print(f"✅ Session supprimée avec succès")
        
        # Vérifier que la session n'existe plus
        response = requests.get(f"{API_URL}/session/{session_id}/info")
        if response.status_code == 404:
            print(f"✅ Confirmation: session introuvable (normal)")
            return True
        else:
            print(f"⚠️ La session existe encore")
            return False
    else:
        print(f"❌ Erreur: {response.status_code}")
        return False

def test_sessions_stats():
    """Test des statistiques de sessions."""
    print("\n📈 Test: Statistiques des sessions")
    
    response = requests.get(f"{API_URL}/sessions/stats")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Sessions actives: {data['active_sessions']}")
        return True
    else:
        print(f"❌ Erreur: {response.status_code}")
        return False

def main():
    """Fonction principale pour lancer tous les tests."""
    print("=" * 60)
    print("🧪 TESTS DU SYSTÈME DE SESSIONS")
    print("=" * 60)
    
    # Vérifier que le serveur est accessible
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code != 200:
            print("\n❌ Le serveur n'est pas accessible.")
            print("Lancez le serveur avec: python main.py")
            return
    except requests.exceptions.ConnectionError:
        print("\n❌ Impossible de se connecter au serveur.")
        print("Assurez-vous que le serveur est lancé avec: python main.py")
        return
    
    print("\n✅ Le serveur est en ligne!")
    
    # Liste des tests
    results = []
    
    # Test 1: Création de session
    session_id = test_session_creation()
    results.append(("Création de session", session_id is not None))
    
    if session_id:
        time.sleep(1)
        
        # Test 2: Chat avec session
        results.append(("Chat avec session", test_session_chat(session_id)))
        time.sleep(1)
        
        # Test 3: Informations de session
        results.append(("Informations de session", test_session_info(session_id)))
        time.sleep(1)
        
        # Test 4: Suppression de session
        results.append(("Suppression de session", test_session_deletion(session_id)))
        time.sleep(1)
    
    # Test 5: Contexte de conversation
    results.append(("Maintien du contexte", test_conversation_context()))
    time.sleep(1)
    
    # Test 6: Chat sans session_id
    results.append(("Création automatique", test_session_without_id()))
    time.sleep(1)
    
    # Test 7: Statistiques
    results.append(("Statistiques", test_sessions_stats()))
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    for test_name, success in results:
        status = "✅ SUCCÈS" if success else "❌ ÉCHEC"
        print(f"{status} - {test_name}")
    
    success_rate = sum(1 for _, s in results if s) / len(results) * 100
    print(f"\nTaux de réussite: {success_rate:.0f}%")
    
    if success_rate == 100:
        print("\n🎉 Tous les tests ont réussi! Le système de sessions fonctionne parfaitement.")
    elif success_rate >= 70:
        print("\n⚠️ La plupart des tests ont réussi, mais certains ont échoué.")
    else:
        print("\n❌ De nombreux tests ont échoué. Vérifiez la configuration.")
    
    print("\n💡 Conseil: Ouvrez index.html dans votre navigateur pour tester l'interface!")

if __name__ == "__main__":
    main()
