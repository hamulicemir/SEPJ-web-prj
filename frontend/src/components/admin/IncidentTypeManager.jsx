import { useState } from "react";
import { Card, Textarea, TextInput, Button } from "flowbite-react";
import { mockIncidentTypes } from "../../mock/incidentTypes";

export default function IncidentTypeManager() {
  const [items, setItems] = useState(mockIncidentTypes);
  const [selected, setSelected] = useState(null);

  const [form, setForm] = useState({
    name: "",
    description: "",
    prompt_ref: "",
  });

  const handleSelect = (item) => {
    setSelected(item);

    setForm({
      name: item.name,
      description: item.description,
      prompt_ref: item.prompt_ref,
    });
  };

  const handleSave = () => {
    console.log("SAVE INCIDENT TYPE TO BACKEND:", {
      code: selected.code,
      ...form,
    });

    setItems((prev) =>
      prev.map((i) =>
        i.code === selected.code ? { ...i, ...form } : i
      )
    );
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* LEFT */}
      <Card className="md:col-span-1">
        <h2 className="text-xl font-bold mb-3">Vorfallstypen</h2>

        <div className="space-y-2">
          {items.map((i) => (
            <button
              key={i.code}
              onClick={() => handleSelect(i)}
              className={`w-full text-left px-3 py-2 rounded border 
                ${selected?.code === i.code ? "bg-blue-100 border-blue-400" : "border-gray-300"}
              `}
            >
              <div className="font-semibold">{i.name}</div>
              <div className="text-sm text-gray-600">{i.code}</div>
            </button>
          ))}
        </div>
      </Card>

      {/* RIGHT */}
      <Card className="md:col-span-2 p-4">
        {selected ? (
          <>
            <h2 className="text-xl font-bold mb-3">{selected.name} bearbeiten</h2>

            <div className="space-y-4">

              <div>
                <label className="font-semibold">Name</label>
                <TextInput
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                />
              </div>

              <div>
                <label className="font-semibold">Beschreibung</label>
                <Textarea
                  rows={4}
                  value={form.description}
                  onChange={(e) =>
                    setForm({ ...form, description: e.target.value })
                  }
                />
              </div>

              <div>
                <label className="font-semibold">Prompt-Referenz</label>
                <TextInput
                  value={form.prompt_ref}
                  onChange={(e) =>
                    setForm({ ...form, prompt_ref: e.target.value })
                  }
                />
              </div>

              <Button color="blue" onClick={handleSave}>
                Speichern
              </Button>
            </div>
          </>
        ) : (
          <p className="text-gray-500">Bitte einen Vorfallstyp auswählen.</p>
        )}
      </Card>
    </div>
  );
}
