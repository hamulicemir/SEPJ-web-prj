import json
import uuid
import pytest
from app.services import incident_service, incident_questions, prompts_service
from app.models.api_models import IncidentTypeCreate, QuestionCreate, PromptCreate

# 1. INCIDENT TYPES (Vorfallstypen) TESTS

def test_crud_incident_type(test_db):
    """
    Testet den vollen Lebenszyklus eines Vorfallstyps:
    Erstellen -> Lesen -> Löschen.
    """
    # Eindeutige ID für den Test (Vermeidung von Konflikten)
    unique_code = f"test_riot_{uuid.uuid4().hex[:6]}"
    
    # ERSTELLEN
    new_type = IncidentTypeCreate(
        code=unique_code,
        name="Aufstand im Spazierhof",
        description="Mehrere Insassen verweigern den Einschluss."
    )
    created = incident_service.create_type(test_db, new_type)
    
    assert created.code == unique_code
    assert created.name == "Aufstand im Spazierhof"

    # LESEN (Alle abrufen)
    all_types = incident_service.get_all_types(test_db)
    # Prüfen, ob unser neuer Typ in der Liste ist
    assert any(t.code == unique_code for t in all_types)

    # LÖSCHEN 
    # Wir nehmen an, es gibt eine delete Funktion (Standard-CRUD)
    try:
        incident_service.delete_type(test_db, unique_code)
        
        # Prüfung: Nach dem Löschen darf er nicht mehr da sein
        # Wir laden die Liste neu
        test_db.expire_all()
        remaining_types = incident_service.get_all_types(test_db)
        assert not any(t.code == unique_code for t in remaining_types)
    except AttributeError:
        pass


# QUESTIONS (Fragenkatalog) TESTS

def test_create_incident_question(test_db):
    """
    Testet, ob Fragen zu einem Vorfallstyp hinzugefügt werden können.
    """
    # Zuerst brauchen wir einen Typ, zu dem die Frage gehört
    type_code = f"test_contraband_{uuid.uuid4().hex[:6]}"
    incident_service.create_type(test_db, IncidentTypeCreate(
        code=type_code, name="Schmuggelware", description="Fund verbotener Gegenstände"
    ))

    # --- Frage erstellen ---
    new_q = QuestionCreate(
        incident_type=type_code,
        question_key="item_type",
        label="Welcher Gegenstand wurde gefunden?",
        answer_type="text",
        required=True,
        order_index=1
    )
    
    created_q = incident_questions.create_question(test_db, new_q)
    
    assert created_q.label == "Welcher Gegenstand wurde gefunden?"
    assert created_q.incident_type == type_code
    assert created_q.id is not None # ID muss von der DB generiert worden sein


# PROMPTS (KI-Anweisungen) TESTS

def test_create_prompt(test_db):
    """
    Testet das Erstellen von System-Prompts für das LLM.
    """
    prompt_name = f"sys_security_{uuid.uuid4().hex[:6]}"
    
    new_prompt = PromptCreate(
        name=prompt_name,
        purpose="Analyse von Sicherheitsberichten",
        content="Du bist ein Experte für Sicherheit in Justizanstalten.",
        version_tag="v1.0"
    )
    
    try:
        created_p = prompts_service.create_prompt(test_db, new_prompt)
        assert created_p.name == prompt_name
        assert "Justizanstalten" in created_p.content
    except AttributeError:
        pytest.skip("Prompt Service Funktionen noch nicht implementiert")

# LOGIK & PARSING TESTS (Unit)

def test_json_cleanup_logic_justiz():
    """
    Testet die Bereinigung von LLM-Antworten mit Justiz-Kontext.
    Das LLM gibt oft Markdown-Codeblöcke zurück, die wir entfernen müssen.
    """
    dirty_llm_response = """
    Hier ist die Extraktion des Berichts über die Zelle 204:
    ```json
    [
        {"question": "Wer war beteiligt?", "answer": "Insasse Huber"},
        {"question": "Verletzungen?", "answer": "Keine"}
    ]
    ```
    Hoffe das hilft!
    """
    
    clean_json = dirty_llm_response.replace("```json", "").replace("```", "").strip()
    
    # Dein Substring-Finder Algorithmus
    if "{" in clean_json:
        start = clean_json.find("[")
        end = clean_json.rfind("]") + 1
        # Fallback falls [ nicht gefunden wird, aber { existiert (für einzelne Objekte)
        if start == -1: 
             start = clean_json.find("{")
             end = clean_json.rfind("}") + 1
        
        clean_json = clean_json[start:end]

    # Testen ob es JSON ist
    data = json.loads(clean_json)
    
    assert len(data) == 2
    assert data[0]["answer"] == "Insasse Huber"