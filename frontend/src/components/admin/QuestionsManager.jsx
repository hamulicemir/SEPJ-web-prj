import { useState } from "react";
import { Card, Button, TextInput, Select, Checkbox } from "flowbite-react";
import { mockIncidentTypes } from "../../mock/incidentTypes";
import { mockQuestions } from "../../mock/questions";

export default function QuestionsManager() {
  const [selectedType, setSelectedType] = useState(null);

  const [questions, setQuestions] = useState(mockQuestions);

  // Nur Fragen des ausgewählten Typs
  const filteredQuestions = selectedType
    ? questions
        .filter((q) => q.incident_type === selectedType.code)
        .sort((a, b) => a.order_index - b.order_index)
    : [];

  const handleUpdate = (id, field, value) => {
    setQuestions((prev) =>
      prev.map((q) => (q.id === id ? { ...q, [field]: value } : q))
    );
  };

  const handleAddQuestion = () => {
    const newQ = {
      id: crypto.randomUUID(),
      incident_type: selectedType.code,
      question_key: "new_question",
      label: "Neue Frage",
      answer_type: "string",
      required: false,
      order_index: filteredQuestions.length * 10 + 10
    };

    setQuestions((prev) => [...prev, newQ]);
  };

  const handleDelete = (id) => {
    setQuestions((prev) => prev.filter((q) => q.id !== id));
  };

  return (
    <div className="space-y-6">

      {/* Vorfallstyp Auswahl */}
      <Card>
        <h2 className="text-xl font-semibold mb-4">Vorfallstyp auswählen</h2>

        <Select
          onChange={(e) =>
            setSelectedType(
              mockIncidentTypes.find((t) => t.code === e.target.value)
            )
          }
        >
          <option value="">-- Bitte wählen --</option>
          {mockIncidentTypes.map((t) => (
            <option key={t.code} value={t.code}>
              {t.name}
            </option>
          ))}
        </Select>
      </Card>

      {selectedType && (
        <Card>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-bold">
              Fragen für: {selectedType.name}
            </h3>

            <Button color="blue" size="sm" onClick={handleAddQuestion}>
              Frage hinzufügen
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
                    <label className="font-semibold">Key</label>
                    <TextInput
                      value={q.question_key}
                      onChange={(e) =>
                        handleUpdate(q.id, "question_key", e.target.value)
                      }
                    />
                  </div>

                  <div>
                    <label className="font-semibold">Label</label>
                    <TextInput
                      value={q.label}
                      onChange={(e) =>
                        handleUpdate(q.id, "label", e.target.value)
                      }
                    />
                  </div>

                  <div>
                    <label className="font-semibold">Antworttyp</label>
                    <Select
                      value={q.answer_type}
                      onChange={(e) =>
                        handleUpdate(q.id, "answer_type", e.target.value)
                      }
                    >
                      <option value="string">String</option>
                      <option value="datetime">Date/Time</option>
                      <option value="people[]">Personenliste</option>
                    </Select>
                  </div>

                  <div>
                    <label className="font-semibold">Reihenfolge</label>
                    <TextInput
                      type="number"
                      value={q.order_index}
                      onChange={(e) =>
                        handleUpdate(q.id, "order_index", Number(e.target.value))
                      }
                    />
                  </div>

                  <div className="flex items-center gap-2">
                    <Checkbox
                      checked={q.required}
                      onChange={(e) =>
                        handleUpdate(q.id, "required", e.target.checked)
                      }
                    />
                    <span>Pflichtfeld</span>
                  </div>
                </div>

                <Button
                  color="failure"
                  size="xs"
                  onClick={() => handleDelete(q.id)}
                  className="mt-4"
                >
                  Löschen
                </Button>

              </Card>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
