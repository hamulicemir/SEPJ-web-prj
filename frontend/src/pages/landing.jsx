import { useState, useEffect } from "react";
import ReportModal from "../components/ReportModal";
import HistoryItem from "../components/HistoryItem";

export default function LandingPage() {
  const [text, setText] = useState("");
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);

  const fetchHistory = () => {
    fetch("http://localhost:8000/api/reports/history")
      .then((res) => res.json())
      .then((data) => setHistory(data))
      .catch((err) => console.error("Fehler beim Laden der History:", err));
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleAnalyze = async () => {
    console.log("Analyse gestartet...");

    if (!text.trim()) {
      alert("Bitte Text eingeben!");
      return;
    }

    setLoading(true);
    setResponse(null);

    try {
      const res = await fetch("http://localhost:8000/api/llm/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Fehler bei der Analyse");
      }

      const data = await res.json();
      setResponse(data);
      fetchHistory();
    } catch (error) {
      console.error(error);
      alert("Fehler: " + error.message);
      setResponse({ final_report: "Fehler: " + error.message });
    } finally {
      setLoading(false);
    }
  };

  const restoreReport = (report) => {
    setText(report.full_text || "");
    setResponse(null);
    setSelectedReport(null);
  };

  return (
    // FIX: calc(100vh - NavbarHöhe)
    <div className="flex h-[calc(100vh-64px)] overflow-hidden bg-gray-50 font-sans">
      <ReportModal
        report={selectedReport}
        onClose={() => setSelectedReport(null)}
        onRestore={restoreReport}
      />

      {/* --- SIDEBAR --- */}
      <div className="w-80 2xl:w-96 bg-white border-r border-gray-200 flex flex-col shadow-xl z-20 flex-shrink-0 transition-all duration-300">
        <div className="p-4 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
          <h2 className="font-bold text-gray-700 2xl:text-lg">Verlauf</h2>
          <button
            onClick={fetchHistory}
            className="text-blue-600 hover:text-blue-800 text-xs 2xl:text-sm"
          >
            ↻
          </button>
        </div>

        <div className="flex-1 overflow-y-auto scrollbar-thin">
          {history.length === 0 ? (
            <div className="p-4 text-center text-sm text-gray-400">
              Keine Berichte gefunden.
            </div>
          ) : (
            history.map((item) => (
              <HistoryItem
                key={item.id}
                item={item}
                onClick={setSelectedReport}
              />
            ))
          )}
        </div>
      </div>

      {/* --- MAIN CONTENT --- */}
      <div className="flex-1 flex flex-col h-full overflow-hidden relative">
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-5xl 2xl:max-w-7xl mx-auto space-y-6 pb-20 transition-all duration-300">
            <div className="text-center mb-6">
              <h1 className="text-3xl 2xl:text-4xl font-bold text-gray-800">
                AI Berichtsgenerator
              </h1>
            </div>

            {/* --- EINGABE CARD --- */}
            <div className="bg-white p-6 2xl:p-8 rounded-lg shadow-sm border border-gray-200">
              <label className="block text-lg 2xl:text-xl font-semibold text-gray-700 mb-3">
                Sachverhalt eingeben
              </label>

              <textarea
                className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-base 2xl:text-lg resize-none leading-relaxed"
                style={{ minHeight: "50vh" }}
                placeholder="Hier den Berichtstext eingeben..."
                value={text}
                onChange={(e) => setText(e.target.value)}
              />

              <div className="mt-4 flex justify-end">
                <button
                  onClick={handleAnalyze}
                  disabled={loading || !text.trim()}
                  className={`
                    px-6 py-3 2xl:px-8 2xl:py-4 rounded-lg text-white font-semibold shadow-md transition-all 2xl:text-lg
                    ${loading || !text.trim()
                      ? "bg-gray-400 cursor-not-allowed"
                      : "bg-blue-600 hover:bg-blue-700 hover:shadow-lg"
                    }
                  `}
                >
                  {loading ? "Analysiere..." : "Bericht analysieren"}
                </button>
              </div>
            </div>

            {/* --- DOWNLOAD BEREICH --- */}
            {response && (
              <div className="animate-fade-in space-y-6">

                {/* PDF DOWNLOAD CARD */}
                <div className="bg-white p-8 2xl:p-10 rounded-lg shadow-xl border-l-4 border-green-500">
                  <div className="flex flex-col items-center justify-center py-4 text-center space-y-4">

                    {/* Icon */}
                    <div className="bg-green-100 p-4 rounded-full">
                      <span className="text-4xl">✅</span>
                    </div>

                    <h2 className="text-2xl font-bold text-gray-800">
                      Analyse abgeschlossen
                    </h2>

                    <p className="text-gray-600 max-w-lg text-lg">
                      Der Vorfall wurde erfolgreich analysiert und ein formaler Bericht erstellt.
                      Sie können das Dokument nun herunterladen.
                    </p>

                    {/* Download Button */}
                    {response.raw_report_id && (
                      <a
                        href={`http://localhost:8000/api/reports/${response.raw_report_id}/pdf`}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <button className="mt-4 px-8 py-4 bg-green-600 hover:bg-green-700 text-white font-bold rounded-lg shadow-md transition-transform hover:scale-105 text-lg">
                          Vorfallsbericht als PDF herunterladen
                        </button>
                      </a>
                    )}
                  </div>
                </div>

                {/* PROMPT DEBUG CARD */}
                <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
                  <h2 className="text-lg font-semibold mb-2 text-gray-800">
                    Generierter Prompt (Debug)
                  </h2>
                  <div className="bg-gray-50 p-4 rounded text-xs text-gray-500 font-mono overflow-x-auto">
                    <details>
                      <summary className="cursor-pointer hover:text-gray-700">
                        Technischen Prompt anzeigen
                      </summary>
                      <div className="mt-2 whitespace-pre-wrap">
                        {response.prompt || "Kein Prompt verfügbar."}
                      </div>
                    </details>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}