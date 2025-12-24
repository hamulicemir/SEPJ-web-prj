import { useState, useEffect } from "react";
import { Card, TextInput, Textarea, Button, Modal } from "flowbite-react";

export default function IncidentTypeManager() {
  const [types, setTypes] = useState([]);
  const [selected, setSelected] = useState(null);
  const [isCreating, setIsCreating] = useState(false);

  // Modal State
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteCandidate, setDeleteCandidate] = useState(null);

  const [formData, setFormData] = useState({
    code: "",
    name: "",
    description: "",
    prompt_ref: "",
  });

  useEffect(() => {
    fetchTypes();
  }, []);

  const fetchTypes = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/config/types");
      if (res.ok) setTypes(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  const handleSelect = (t) => {
    setIsCreating(false);
    setSelected(t);
    setFormData(t);
  };

  const handleCreateNew = () => {
    setSelected(null);
    setIsCreating(true);
    setFormData({ code: "", name: "", description: "", prompt_ref: "" });
  };

  const handleCancel = () => {
    setIsCreating(false);
    setSelected(null);
    setFormData({ code: "", name: "", description: "", prompt_ref: "" });
  };

  const confirmDelete = (code) => {
    setDeleteCandidate(code);
    setShowDeleteModal(true);
  };

  const executeDelete = async () => {
    if (!deleteCandidate) return;
    try {
      await fetch(`http://localhost:8000/api/config/types/${deleteCandidate}`, {
        method: "DELETE",
      });
      await fetchTypes();
      handleCancel();
    } catch (e) {
      alert("Fehler beim Löschen");
    } finally {
      setShowDeleteModal(false);
      setDeleteCandidate(null);
    }
  };

  const handleSave = async () => {
    if (isCreating && !formData.code.trim()) {
      alert("Bitte einen Code eingeben.");
      return;
    }

    const url = isCreating
      ? "http://localhost:8000/api/config/types"
      : `http://localhost:8000/api/config/types/${formData.code}`;

    try {
      const res = await fetch(url, {
        method: isCreating ? "POST" : "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (res.ok) {
        await fetchTypes();
        if (isCreating) {
          alert("Erstellt!");
          handleCancel();
        } else {
          alert("Gespeichert!");
        }
      } else {
        alert("Fehler beim Speichern");
      }
    } catch (e) {
      alert("Netzwerkfehler");
    }
  };

  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* LISTE */}
        <Card className="md:col-span-1">
          <div className="flex justify-between items-center mb-2">
            <h2 className="text-xl font-bold">Typen</h2>
            <Button size="xs" color="success" onClick={handleCreateNew}>
              + Neu
            </Button>
          </div>
          <div className="space-y-2 overflow-y-auto h-96 pr-2">
            {types.map((t) => (
              <div
                key={t.code}
                onClick={() => handleSelect(t)}
                className={`p-2 border rounded cursor-pointer hover:bg-gray-50 
                  ${
                    selected?.code === t.code
                      ? "bg-blue-50 border-blue-500"
                      : ""
                  }
                `}
              >
                <div className="font-bold">{t.name}</div>
                <div className="text-xs text-gray-500 truncate">{t.code}</div>
              </div>
            ))}
          </div>
        </Card>

        {/* EDITOR */}
        <Card className="md:col-span-2">
          {selected || isCreating ? (
            <div className="flex flex-col gap-4">
              <h2 className="text-xl font-bold border-b pb-2">
                {isCreating
                  ? "Neuen Typ anlegen"
                  : `Bearbeiten: ${selected.name}`}
              </h2>

              <div>
                <label className="block text-sm font-medium mb-1">
                  Code (ID)
                </label>
                <TextInput
                  value={formData.code}
                  onChange={(e) =>
                    setFormData({ ...formData, code: e.target.value })
                  }
                  disabled={!isCreating}
                  placeholder="z.B. water_damage"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Name</label>
                <TextInput
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">
                  Beschreibung
                </label>
                <Textarea
                  value={formData.description || ""}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  rows={4}
                />
              </div>

              <div className="flex justify-between mt-4 pt-4 border-t">
                <Button color="gray" onClick={handleCancel}>
                  Abbrechen
                </Button>
                <div className="flex gap-2">
                  {!isCreating && (
                    <Button
                      color="failure"
                      onClick={() => confirmDelete(formData.code)}
                    >
                      Löschen
                    </Button>
                  )}
                  <Button onClick={handleSave} color="blue">
                    {isCreating ? "Erstellen" : "Speichern"}
                  </Button>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-400 min-h-[200px]">
              Wähle einen Typ oder erstelle einen neuen.
            </div>
          )}
        </Card>
      </div>

      {/* FLOWBITE MODAL (ersetzt Custom-Modal) */}
      <Modal
        show={showDeleteModal}
        size="md"
        popup
        onClose={() => setShowDeleteModal(false)}
      >
        <div className="bg-white rounded-lg p-6 shadow-xl max-w-sm w-full mx-auto">
          <h3 className="text-lg font-normal text-gray-500 mb-6 text-center">
            Wirklich löschen?
          </h3>
          <div className="flex justify-center gap-4">
            <Button color="failure" onClick={executeDelete}>
              Ja, löschen
            </Button>
            <Button color="gray" onClick={() => setShowDeleteModal(false)}>
              Abbrechen
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
}
