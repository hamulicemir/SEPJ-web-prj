import { useState } from "react";
import PromptManager from "../components/admin/PromptManager";
import IncidentTypeManager from "../components/admin/IncidentTypeManager";
import QuestionsManager from "../components/admin/QuestionsManager.jsx";
import { Button } from "flowbite-react";

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState("prompts");

  return (
    <div className="max-w-6xl mx-auto p-6">

      {/* TAB NAVIGATION */}
      <div className="flex gap-4 mb-6 border-b pb-3">
        <Button
          color={activeTab === "prompts" ? "blue" : "gray"}
          onClick={() => setActiveTab("prompts")}
        >
          Prompts
        </Button>

        <Button
          color={activeTab === "incidentTypes" ? "blue" : "gray"}
          onClick={() => setActiveTab("incidentTypes")}
        >
          Vorfallstypen
        </Button>
        <Button
          color={activeTab === "questions" ? "blue" : "gray"}
          onClick={() => setActiveTab("questions")}
        >
          Fragen
        </Button>
      </div>

      {/* DYNAMIC CONTENT */}
      {activeTab === "prompts" && <PromptManager />}
      {activeTab === "incidentTypes" && <IncidentTypeManager />}
      {activeTab === "questions" && <QuestionsManager />}
    </div>
  );
}
