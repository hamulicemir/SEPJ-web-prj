import { useState, useEffect } from "react";
import { Card, Button, TextInput, Select, Checkbox, Modal, Label } from "flowbite-react";

export default function QuestionsManager() {
  const [types, setTypes] = useState([]);
  const [questions, setQuestions] = useState([]);
  
  const [selectedTypeCode, setSelectedTypeCode] = useState("");
  const [selectedQuestion, setSelectedQuestion] = useState(null);
  const [isCreating, setIsCreating] = useState(false);

  // Modal State
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteId, setDeleteId] = useState(null);

  // Form Data State
  const [formData, setFormData] = useState({});

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

  const handleTypeChange = (e) => {
    setSelectedTypeCode(e.target.value);
    handleCancel(); 
  };

  const handleSelectQuestion = (q) => {
    setIsCreating(false);
    setSelectedQuestion(q);
    setFormData({ ...q });
  };

  const handleCreateNew = () => {
    if (!selectedTypeCode) {
        alert("Bitte wählen Sie zuerst einen Vorfallstyp aus der Liste.");
        return;
    }

    setIsCreating(true);
    setSelectedQuestion(null);
    setFormData({
      incident_type: selectedTypeCode,
      question_key: "",
      label: "",
      answer_type: "string",
      required: false,
      order_index: filteredQuestions.length * 10 + 10,
    });
  };

  const handleCancel = () => {
    setSelectedQuestion(null);
    setIsCreating(false);
    setFormData({});
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = async () => {
    const url = isCreating 
        ? "http://localhost:8000/api/config/questions"
        : `http://localhost:8000/api/config/questions/${formData.id}`;
    
    try {
        const res = await fetch(url, {
            method: isCreating ? "POST" : "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(formData)
        });

        if (res.ok) {
            const savedQ = await res.json();
            if (isCreating) {
                setQuestions(prev => [...prev, savedQ]);
                alert("Erstellt!");
                handleCancel();
            } else {
                setQuestions(prev => prev.map(q => q.id === savedQ.id ? savedQ : q));
                alert("Gespeichert!");
                setSelectedQuestion(null);
                setIsCreating(false);
            }
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
    try {
        await fetch(`http://localhost:8000/api/config/questions/${deleteId}`, { method: "DELETE" });
        setQuestions(prev => prev.filter(q => q.id !== deleteId));
        handleCancel();
    } catch(e) { alert("Fehler beim Löschen"); }
    finally {
        setShowDeleteModal(false);
        setDeleteId(null);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-150px)] gap-4">
      
      <Card className="flex-shrink-0">
        <div className="flex justify-between items-center mb-2">
            <h2 className="text-xl font-semibold">Vorfallstyp auswählen</h2>
            <Button color="blue" onClick={handleCreateNew}>
                + Neu
            </Button>
        </div>
        <Select value={selectedTypeCode} onChange={handleTypeChange}>
          <option value="">-- Bitte wählen --</option>
          {types.map((t) => (
            <option key={t.code} value={t.code}>{t.name}</option>
          ))}
        </Select>
      </Card>

      {selectedTypeCode && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 flex-grow overflow-hidden">
            
            <Card className="md:col-span-1 flex flex-col overflow-hidden h-full">
                <div className="flex justify-between items-center mb-2 flex-shrink-0">
                    <h3 className="text-lg font-bold">Fragen ({filteredQuestions.length})</h3>
                </div>
                
                <div className="overflow-y-auto flex-grow space-y-2 pr-1">
                    {filteredQuestions.length === 0 && (
                        <p className="text-gray-500 text-sm">Keine Fragen vorhanden.</p>
                    )}
                    {filteredQuestions.map((q) => (
                        <div 
                            key={q.id}
                            onClick={() => handleSelectQuestion(q)}
                            className={`p-3 border rounded cursor-pointer transition-colors
                                ${selectedQuestion?.id === q.id 
                                    ? "bg-blue-50 border-blue-500 ring-1 ring-blue-500" 
                                    : "hover:bg-gray-50 bg-white"
                                }
                            `}
                        >
                            <div className="font-semibold text-sm">{q.label}</div>
                            <div className="text-xs text-gray-400 flex justify-between mt-1">
                                <span>{q.question_key}</span>
                                <span>Idx: {q.order_index}</span>
                            </div>
                        </div>
                    ))}
                </div>
            </Card>

            <Card className="md:col-span-2 flex flex-col overflow-y-auto h-full">
                {(selectedQuestion || isCreating) ? (
                    <div className="space-y-4">
                        <h3 className="text-xl font-bold border-b pb-2">
                            {isCreating ? "Neue Frage anlegen" : "Frage bearbeiten"}
                        </h3>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <Label value="Key (Technisch)" className="mb-1 block"/>
                                <TextInput
                                    size="sm"
                                    value={formData.question_key || ""}
                                    onChange={(e) => handleChange("question_key", e.target.value)}
                                    placeholder="z.B. who_involved"
                                />
                            </div>

                            <div>
                                <Label value="Label (Frage)" className="mb-1 block"/>
                                <TextInput
                                    size="sm"
                                    value={formData.label || ""}
                                    onChange={(e) => handleChange("label", e.target.value)}
                                    placeholder="z.B. Wer war beteiligt?"
                                />
                            </div>

                            <div>
                                <Label value="Antworttyp" className="mb-1 block"/>
                                <Select
                                    size="sm"
                                    value={formData.answer_type || "string"}
                                    onChange={(e) => handleChange("answer_type", e.target.value)}
                                >
                                    <option value="string">Textzeile (String)</option>
                                    <option value="text">Textblock (Mehrzeilig)</option>
                                    <option value="datetime">Datum/Zeit</option>
                                    <option value="people[]">Personenliste</option>
                                    <option value="boolean">Ja/Nein</option>
                                </Select>
                            </div>

                            <div>
                                <Label value="Reihenfolge" className="mb-1 block"/>
                                <TextInput
                                    size="sm"
                                    type="number"
                                    value={formData.order_index || 0}
                                    onChange={(e) => handleChange("order_index", Number(e.target.value))}
                                />
                            </div>
                        </div>

                        <div className="flex items-center gap-2 mt-2">
                            <Checkbox
                                id="req"
                                checked={formData.required || false}
                                onChange={(e) => handleChange("required", e.target.checked)}
                            />
                            <Label color="black" htmlFor="req">Pflichtfeld</Label>
                        </div>

                        <div className="flex justify-between mt-6 pt-4 border-t">
                            <Button color="gray" onClick={handleCancel}>
                                Abbrechen
                            </Button>
                            
                            <div className="flex gap-2">
                                {!isCreating && (
                                    <Button color="failure" outline onClick={() => confirmDelete(formData.id)}>
                                        Löschen
                                    </Button>
                                )}
                                <Button color="blue" onClick={handleSave}>
                                    {isCreating ? "Erstellen" : "Speichern"}
                                </Button>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center h-full text-gray-400">
                        <p>Wähle eine Frage aus der Liste links</p>
                        <p className="text-sm">oder klicke oben auf "+ Neu"</p>
                    </div>
                )}
            </Card>
        </div>
      )}

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