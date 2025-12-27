import React, { useState } from "react";
import { Label, Textarea, Card, Button } from "flowbite-react";
import axios from "axios";

export default function Landing() {
  const [message, setMessage] = useState("");
  const [prompt, setPrompt] = useState("");

  // initial value "null", to know when we have data
  const [response, setResponse] = useState(null);

  const [loading, setLoading] = useState(false);

  const analyzeReport = async () => {
    setLoading(true);
    setPrompt("");
    setResponse(null);

    try {
      const res = await axios.post("http://localhost:8000/api/llm/analyze", {
        text: message,
      });

      setResponse(res.data);
      setPrompt(res.data.prompt);
    } catch (err) {
      console.error(err);
      // Fallback when Error: simple object, to prevent the display from crashing
      setResponse({ final_report: "Fehler beim Abruf der Analyse." });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900" data-theme="light">
      <div className="flex flex-col items-center justify-center px-6 py-10 space-y-8 pt-4">

        {/* Eingabe Card*/}
        <Card className="w-full max-w-4xl bg-white shadow-lg p-10 min-h-[50vh]">
          <h1 className="text-3xl font-semibold mb-2 text-gray-800">
            Texteingabe des Berichts
          </h1>

          <div className="flex flex-col gap-3">
            <Label htmlFor="message" value="Your message" className="text-lg" />
            <Textarea
              id="message"
              rows={12}
              placeholder="Write your thoughts here..."
              className="min-h-[40vh] bg-white !text-gray-900 border-gray-300 focus:ring-blue-500 focus:border-blue-500"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
            />
          </div>
          <div className="flex justify-end mt-1">
            <Button
              color="blue"
              onClick={analyzeReport}
              disabled={!message.trim() || loading}
            >
              {loading ? "Analysiere..." : "Bericht analysieren"}
            </Button>
          </div>
        </Card>

        {/* Ausgabe Card */}
        <Card className="w-full max-w-4xl bg-white shadow-md p-2">
          <h2 className="text-2xl font-semibold mb-2 text-gray-800">
            Berichtsausgabe
          </h2>

          <div className="text-gray-700">
            {!response ? (
              <p>Noch keine Analyse durchgeführt.</p>
            ) : (
              <div className="space-y-6">

                {/* formal Report*/}
                {response.final_report && (
                  <div className="bg-gray-50 p-4 rounded border border-gray-200">
                    <h3 className="font-bold text-gray-800 mb-2">Formaler Polizeibericht</h3>
                    <div className="whitespace-pre-wrap font-serif leading-relaxed">
                      {response.final_report}
                    </div>
                  </div>
                )}

                {/* B) facts & classification */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

                  {/* classification */}
                  {response.result && (
                    <div className="bg-blue-50 p-3 rounded border border-blue-100">
                      <strong className="block text-blue-800 mb-1">Klassifikation:</strong>
                      <div className="flex flex-wrap gap-1">
                        {Array.isArray(response.result) ? response.result.map((r, i) => (
                          <span key={i} className="bg-white px-2 py-0.5 rounded text-sm border border-blue-200">{r}</span>
                        )) : response.result}
                      </div>
                    </div>
                  )}

                  {/* facts / replies */}
                  {response.answers && (
                    <div className="bg-yellow-50 p-3 rounded border border-yellow-100">
                      <strong className="block text-yellow-800 mb-1">Details:</strong>
                      <div className="text-sm space-y-2">
                        {Object.entries(response.answers).map(([type, facts]) => (
                          <div key={type}>
                            <span className="uppercase text-xs font-bold text-gray-500">{type}</span>
                            <ul className="pl-2">
                              {Object.entries(facts).map(([k, v]) => (
                                <li key={k}><span className="font-medium">{k}:</span> {v}</li>
                              ))}
                            </ul>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

              </div>
            )}
          </div>
        </Card>

        {/* Prompt Debug Card */}
        <Card className="w-full max-w-4xl bg-white shadow-md p-4">
          <h2 className="text-2xl font-semibold mb-2 text-gray-800">
            Generierter Prompt
          </h2>
          <div className="whitespace-pre-wrap text-gray-700 text-sm font-mono bg-gray-50 p-2 rounded">
            {prompt || "Noch kein Prompt generiert."}
          </div>
        </Card>
      </div>
    </div>
  );
}