import { useState, useEffect } from "react";
import { Card, Button, TextInput, Select, Checkbox, Modal } from "flowbite-react";

export default function QuestionsManager() {
  const [types, setTypes] = useState([]);
  const [questions, setQuestions] = useState([]);
  const [selectedTypeCode, setSelectedTypeCode] = useState("");
  
  // Modal State
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteId, setDeleteId] = useState(null);

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    try {
      const resTypes = await fetch("http://localhost:8000/api/config/types");
      if(resTypes.ok) setTypes(await resTypes.json());

      const resQuestions = await fetch("http://localhost:8000/api/config/questions");
      if(resQuestions.ok) setQuestions(await resQuestions.json());
    } catch(e) { console.error(e); }
  };

  const filteredQuestions = selectedTypeCode
    ? questions
        .filter((q) => q.incident_type === selectedTypeCode)
        .sort((a, b) => a.order_index - b.order_index)
    : [];

  const handleUpdate = (id, field, value) => {
    setQuestions((prev) =>
      prev.map((q) => (q.id === id ? { ...q, [field]: value } : q))
    );
  };

  const handleAddQuestion = () => {
    const newQ = {
      id: "new_" + crypto.randomUUID(), 
      incident_type: selectedTypeCode,
      question_key: "new_key",
      label: "Neue Frage",
      answer_type: "string",
      required: false,
      order_index: filteredQuestions.length * 10 + 10,
      isNew: true 
    };
    setQuestions((prev) => [...prev, newQ]);
  };

  const handleSaveQuestion = async (q) => {
    const isNew = q.isNew === true;
    const url = isNew 
        ? "http://localhost:8000/api/config/questions"
        : `http://localhost:8000/api/config/questions/${q.id}`;
    
    const { isNew: _, id, ...payload } = q;

    try {
        const res = await fetch(url, {
            method: isNew ? "POST" : "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            const savedQ = await res.json();
            setQuestions(prev => prev.map(item => item.id === q.id ? savedQ : item));
            alert("Gespeichert!");
        } else {
            alert("Fehler beim Speichern");
        }
    } catch(e) { alert("Netzwerkfehler"); }
  };

  const confirmDelete = (id) => {
    setDeleteId(id);
    setShowDeleteModal(true);
  };

  const executeDelete = async () => {
    if (!deleteId) return;
    
    // Wenn es nur lokal war
    if (deleteId.toString().startsWith("new_")) {
        setQuestions(prev => prev.filter(q => q.id !== deleteId));
        setShowDeleteModal(false);
        setDeleteId(null);
        return;
    }

    try {
        await fetch(`http://localhost:8000/api/config/questions/${deleteId}`, { method: "DELETE" });
        setQuestions(prev => prev.filter(q => q.id !== deleteId));
    } catch(e) { alert("Fehler beim Löschen"); }
    finally {
        setShowDeleteModal(false);
        setDeleteId(null);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <h2 className="text-xl font-semibold mb-4">Vorfallstyp auswählen</h2>
        <Select
          value={selectedTypeCode}
          onChange={(e) => setSelectedTypeCode(e.target.value)}
        >
          <option value="">-- Bitte wählen --</option>
          {types.map((t) => (
            <option key={t.code} value={t.code}>
              {t.name}
            </option>
          ))}
        </Select>
      </Card>

      {selectedTypeCode && (
        <Card>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-bold">
              Fragen verwalten ({filteredQuestions.length})
            </h3>
            <Button color="blue" size="sm" onClick={handleAddQuestion}>
              + Frage hinzufügen
            </Button>
          </div>

          {filteredQuestions.length === 0 && (
            <p className="text-gray-500">Noch keine Fragen vorhanden.</p>
          )}

          <div className="space-y-6">
            {filteredQuestions.map((q) => (
              <Card key={q.id} className="p-4 border border-gray-200">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  
                  <div>
                    <label className="font-semibold text-xs text-gray-500 uppercase">Key (Technisch)</label>
                    <TextInput
                      size="sm"
                      value={q.question_key}
                      onChange={(e) => handleUpdate(q.id, "question_key", e.target.value)}
                    />
                  </div>

                  <div>
                    <label className="font-semibold text-xs text-gray-500 uppercase">Frage (Label)</label>
                    <TextInput
                      size="sm"
                      value={q.label}
                      onChange={(e) => handleUpdate(q.id, "label", e.target.value)}
                    />
                  </div>

                  <div>
                    <label className="font-semibold text-xs text-gray-500 uppercase">Antworttyp</label>
                    <Select
                      size="sm"
                      value={q.answer_type}
                      onChange={(e) => handleUpdate(q.id, "answer_type", e.target.value)}
                    >
                      <option value="string">Textzeile (String)</option>
                      <option value="text">Textblock</option>
                      <option value="datetime">Datum/Zeit</option>
                      <option value="people[]">Personenliste</option>
                      <option value="boolean">Ja/Nein</option>
                    </Select>
                  </div>

                  <div>
                    <label className="font-semibold text-xs text-gray-500 uppercase">Reihenfolge</label>
                    <TextInput
                      size="sm"
                      type="number"
                      value={q.order_index}
                      onChange={(e) => handleUpdate(q.id, "order_index", Number(e.target.value))}
                    />
                  </div>

                  <div className="flex items-center gap-2 mt-6">
                    <Checkbox
                      checked={q.required}
                      onChange={(e) => handleUpdate(q.id, "required", e.target.checked)}
                    />
                    <span className="text-sm font-medium">Pflichtfeld</span>
                  </div>
                </div>

                <div className="flex justify-end gap-2 mt-4 pt-2 border-t">
                    <Button 
                        size="xs" 
                        color="failure" 
                        outline
                        onClick={() => confirmDelete(q.id)}
                    >
                        Löschen
                    </Button>
                    <Button 
                        size="xs" 
                        color="blue" 
                        onClick={() => handleSaveQuestion(q)}
                    >
                        {q.isNew ? "Erstellen" : "Speichern"}
                    </Button>
                </div>

              </Card>
            ))}
          </div>
        </Card>
      )}

      {/* FLOWBITE MODAL */}
      <Modal show={showDeleteModal} size="md" popup onClose={() => setShowDeleteModal(false)}>
        <div className="bg-white rounded-lg p-6 shadow-xl max-w-sm w-full mx-auto">
          <h3 className="text-lg font-normal text-gray-500 mb-6 text-center">
            Frage wirklich löschen?
          </h3>
          <div className="flex justify-center gap-4">
            <Button color="failure" onClick={executeDelete}>Ja, löschen</Button>
            <Button color="gray" onClick={() => setShowDeleteModal(false)}>Abbrechen</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}