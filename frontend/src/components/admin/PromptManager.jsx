import { useState } from "react";
import { Card, Textarea, Button } from "flowbite-react";
import { mockPrompts } from "../../mock/prompts";

export default function PromptManager() {
  const [prompts, setPrompts] = useState(mockPrompts);
  const [selected, setSelected] = useState(null);
  const [editedContent, setEditedContent] = useState("");

  const handleSelect = (prompt) => {
    setSelected(prompt);
    setEditedContent(prompt.content);
  };

  const handleSave = () => {
    console.log("SAVE PROMPT TO BACKEND:", {
      id: selected.id,
      content: editedContent,
    });

    setPrompts((prev) =>
      prev.map((p) =>
        p.id === selected.id ? { ...p, content: editedContent } : p
      )
    );
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* LEFT */}
      <Card className="md:col-span-1">
        <h2 className="text-xl font-bold mb-3">Prompts</h2>

        <div className="space-y-2">
          {prompts.map((p) => (
            <button
              key={p.id}
              onClick={() => handleSelect(p)}
              className={`w-full text-left px-3 py-2 rounded border 
                ${selected?.id === p.id ? "bg-blue-100 border-blue-400" : "border-gray-300"}
              `}
            >
              <div className="font-semibold">{p.name}</div>
              <div className="text-sm text-gray-600">{p.purpose} – {p.version}</div>
            </button>
          ))}
        </div>
      </Card>

      {/* RIGHT */}
      <Card className="md:col-span-2">
        {selected ? (
          <>
            <h2 className="text-xl font-bold mb-3">{selected.name} bearbeiten</h2>

            <Textarea
              rows={12}
              value={editedContent}
              onChange={(e) => setEditedContent(e.target.value)}
              className="mb-4"
            />

            <Button color="blue" onClick={handleSave}>
              Speichern
            </Button>
          </>
        ) : (
          <p className="text-gray-500">Bitte einen Prompt auswählen.</p>
        )}
      </Card>
    </div>
  );
}
