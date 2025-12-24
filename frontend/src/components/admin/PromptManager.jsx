import { useState, useEffect } from "react";
import { Card, Textarea, Button, TextInput, Label, Badge, Modal } from "flowbite-react";

export default function PromptManager() {
  const [prompts, setPrompts] = useState([]);
  const [selected, setSelected] = useState(null);
  const [isCreating, setIsCreating] = useState(false);
  const [loading, setLoading] = useState(false);

  // Modal State
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteId, setDeleteId] = useState(null);

  const [formData, setFormData] = useState({
    name: "", purpose: "", version_tag: "v1", content: ""
  });

  useEffect(() => { fetchPrompts(); }, []);

  const fetchPrompts = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/prompts/");
      if (res.ok) setPrompts(await res.json());
    } catch (err) { console.error(err); }
  };

  const handleSelect = (p) => {
    setIsCreating(false);
    setSelected(p);
    setFormData({ name: p.name, purpose: p.purpose, version_tag: p.version_tag, content: p.content });
  };

  const handleCreateNew = () => {
    setSelected(null);
    setIsCreating(true);
    setFormData({ name: "", purpose: "", version_tag: "v1", content: "" });
  };

  const handleCancel = () => {
    setIsCreating(false);
    setSelected(null);
    setFormData({ name: "", purpose: "", version_tag: "v1", content: "" });
  };

  const confirmDelete = (id) => {
    setDeleteId(id);
    setShowDeleteModal(true);
  };

  const executeDelete = async () => {
    if(!deleteId) return;
    try {
        await fetch(`http://localhost:8000/api/prompts/${deleteId}`, { method: "DELETE" });
        await fetchPrompts();
        handleCancel();
    } catch(e) { alert("Fehler beim Löschen"); }
    finally {
        setShowDeleteModal(false);
        setDeleteId(null);
    }
  };

  const handleSave = async () => {
    if (!formData.name.trim()) { alert("Name fehlt!"); return; }

    setLoading(true);
    const url = isCreating ? "http://localhost:8000/api/prompts/" : `http://localhost:8000/api/prompts/${selected.id}`;
    const method = isCreating ? "POST" : "PUT";

    try {
      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (res.ok) {
        await fetchPrompts();
        if(isCreating) {
            alert("Erstellt!");
            handleCancel();
        } else {
            alert("Gespeichert!");
        }
      } else {
        alert("Fehler beim Speichern");
      }
    } catch (error) { alert("Netzwerkfehler"); } 
    finally { setLoading(false); }
  };

  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 h-[calc(100vh-200px)]">
        <Card className="md:col-span-1 overflow-y-auto">
          <div className="flex justify-between items-center mb-2">
            <h2 className="text-xl font-bold">Prompts</h2>
            <Button size="xs" color="success" onClick={handleCreateNew}>+ Neu</Button>
          </div>
          <div className="space-y-2">
            {prompts.map((p) => (
              <button
                key={p.id}
                onClick={() => handleSelect(p)}
                className={`w-full text-left px-3 py-2 rounded border transition-colors
                  ${selected?.id === p.id ? "bg-blue-100 border-blue-400" : "bg-white border-gray-200 hover:bg-gray-50"}
                `}
              >
                <div className="font-semibold flex justify-between">
                  <span>{p.name}</span>
                  <Badge color="gray">{p.version_tag}</Badge>
                </div>
                <div className="text-xs text-gray-500 truncate">{p.purpose}</div>
              </button>
            ))}
          </div>
        </Card>

        <Card className="md:col-span-2 flex flex-col">
          {(selected || isCreating) ? (
            <div className="flex flex-col h-full gap-4">
              <h2 className="text-xl font-bold border-b pb-2">
                {isCreating ? "Neuen Prompt erstellen" : `Bearbeite: ${formData.name}`}
              </h2>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label value="Name (System-ID)" />
                  <TextInput 
                    value={formData.name}
                    onChange={e => setFormData({...formData, name: e.target.value})}
                  />
                </div>
                <div>
                  <Label value="Zweck" />
                  <TextInput 
                    value={formData.purpose}
                    onChange={e => setFormData({...formData, purpose: e.target.value})}
                  />
                </div>
              </div>

              <div className="flex-grow flex flex-col">
                <Label value="Inhalt" className="mb-1" />
                <Textarea
                  className="flex-grow font-mono text-sm min-h-[300px]"
                  value={formData.content}
                  onChange={(e) => setFormData({...formData, content: e.target.value})}
                />
              </div>

              <div className="flex justify-between mt-auto pt-4 border-t">
                <Button color="gray" onClick={handleCancel}>Abbrechen</Button>
                <div className="flex gap-2">
                  {!isCreating && (
                    <Button color="failure" onClick={() => confirmDelete(selected.id)}>Löschen</Button>
                  )}
                  <Button color="blue" onClick={handleSave} disabled={loading}>
                    {loading ? "Speichert..." : (isCreating ? "Erstellen" : "Speichern")}
                  </Button>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-400">
              Wähle einen Prompt oder erstelle einen neuen.
            </div>
          )}
        </Card>
      </div>

      {/* FLOWBITE MODAL */}
      <Modal show={showDeleteModal} size="md" popup onClose={() => setShowDeleteModal(false)}>
        <div className="bg-white rounded-lg p-6 shadow-xl max-w-sm w-full mx-auto">
          <h3 className="text-lg font-normal text-gray-500 mb-6 text-center">
            Diesen Prompt wirklich unwiderruflich löschen?
          </h3>
          <div className="flex justify-center gap-4">
            <Button color="failure" onClick={executeDelete}>Ja, löschen</Button>
            <Button color="gray" onClick={() => setShowDeleteModal(false)}>Abbrechen</Button>
          </div>
        </div>
      </Modal>
    </>
  );
}