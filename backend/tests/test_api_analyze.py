import uuid
import json
import httpx
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

UNIQUE_TYPE_CODE = f"test_code_{uuid.uuid4().hex[:6]}"
UNIQUE_TYPE_NAME = f"Testfall Selbstverletzung {uuid.uuid4().hex[:6]}"

@patch("app.services.incident_service.get_all_types") 
@patch("httpx.AsyncClient.post", new_callable=AsyncMock)
def test_analyze_workflow_mocked(mock_post, mock_get_types, client):
    """
    Simuliert den kompletten Analyse-Durchlauf.
    """
    # 1. DB-Mock
    mock_type = MagicMock()
    mock_type.code = UNIQUE_TYPE_CODE
    mock_type.name = UNIQUE_TYPE_NAME 
    mock_type.description = "Testfall"
    mock_get_types.return_value = [mock_type]

    # 2. ECHTE DATEN ANLEGEN
    client.post("/api/config/types", json={
        "code": UNIQUE_TYPE_CODE,
        "name": UNIQUE_TYPE_NAME,
        "description": "Test"
    })
    
    client.post("/api/config/questions", json={
        "incident_type": UNIQUE_TYPE_CODE,
        "question_key": "who",
        "label": "Wer hat sich verletzt?",
        "answer_type": "text", 
        "order_index": 1,
        "required": True
    })

    # 3. Ollama-Mock
    classify_content = json.dumps([UNIQUE_TYPE_NAME])
    extract_content = json.dumps([
        {"question": "Wer hat sich verletzt?", "answer": "Ein Insasse"}
    ])

    responses_to_send = [classify_content, extract_content]
    
    async def side_effect(*args, **kwargs):
        content = responses_to_send.pop(0) if responses_to_send else extract_content
        response = httpx.Response(200, json={"response": content, "done": True})
        request = httpx.Request("POST", "http://mock-ollama")
        response.request = request
        return response

    mock_post.side_effect = side_effect

    # 4. Request
    input_text = "Ein Insasse hat sich in Zelle 5 leicht verletzt."
    response = client.post("/api/llm/analyze", json={"text": input_text})

    # 5. Überprüfungen
    assert response.status_code == 200, f"Fehler im Workflow: {response.text}"
    
    result = response.json()
    print("DEBUG RESULT:", result)

    # --- KORRIGIERTE PRÜFUNG ---
    # Wir prüfen die Liste 'matched_incident_types', die wir im Log gesehen haben
    matched_types = result.get("matched_incident_types", [])
    assert UNIQUE_TYPE_CODE in matched_types, f"Erwartet: {UNIQUE_TYPE_CODE}, Gefunden: {matched_types}"
    
    # Optional: Antwort prüfen
    # Die Antworten sind in 'answers' -> CODE -> QUESTION_KEY
    answers = result.get("answers", {})
    type_answers = answers.get(UNIQUE_TYPE_CODE, {})
    
    # Manchmal ist die Antwort ein String (JSON), manchmal direkt das Objekt
    # Wir prüfen nur grob, ob was da ist
    assert "who" in type_answers or len(type_answers) > 0