import uuid
from fastapi.testclient import TestClient

def test_api_create_and_list_incident_types(client):
    """
    Testet den Endpunkt /api/config/types.
    1. Erstellt einen neuen Typ per POST.
    2. Prüft, ob er in der Liste per GET auftaucht.
    """
    rnd_code = f"api_test_type_{uuid.uuid4().hex[:6]}"
    
    payload = {
        "code": rnd_code,
        "name": "API Test Vorfall",
        "description": "Automatisch generierter Test-Eintrag"
    }

    # 1. POST Request (Erstellen)
    response_create = client.post("/api/config/types", json=payload)
    
    # Prüfen: Status 200 OK?
    assert response_create.status_code == 200, f"Fehler beim Erstellen: {response_create.text}"
    
    # Prüfen: Kommt das Objekt zurück?
    created_data = response_create.json()
    assert created_data["code"] == rnd_code
    assert created_data["name"] == "API Test Vorfall"

    # GET Request (Liste Laden)
    response_list = client.get("/api/config/types")
    assert response_list.status_code == 200
    
    all_types = response_list.json()
    
    found_codes = [t["code"] for t in all_types]
    assert rnd_code in found_codes


def test_api_create_question(client):
    """
    Testet den Endpunkt /api/config/questions.
    Muss zuerst einen Typ anlegen, damit die Foreign-Key-Beziehung passt.
    """
    # Vorbereitung: Typ anlegen
    type_code = f"api_test_q_parent_{uuid.uuid4().hex[:6]}"
    client.post("/api/config/types", json={
        "code": type_code, 
        "name": "Eltern-Typ für Frage"
    })

    # Test: Frage anlegen
    question_payload = {
        "incident_type": type_code,
        "question_key": "weapon_type",
        "label": "Welche Waffe?",
        "answer_type": "text",
        "order_index": 1,
        "required": True
    }

    response = client.post("/api/config/questions", json=question_payload)
    
    assert response.status_code == 200
    q_data = response.json()
    
    assert q_data["incident_type"] == type_code
    assert q_data["label"] == "Welche Waffe?"
    assert "id" in q_data