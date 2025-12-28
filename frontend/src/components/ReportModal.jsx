export default function ReportModal({ report, onClose, onRestore }) {
  if (!report) return null;

  const { result_data } = report;

  const getFinalText = () => {
    const final = result_data?.final_report;
    if (!final) return null;
    if (typeof final === "object" && final.annotations) {
      return final.annotations.incidents?.[1]?.text || "Text nicht gefunden";
    }
    return final;
  };

  const finalText = getFinalText();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4 backdrop-blur-sm">
      <div className="bg-white w-full max-w-5xl h-[90vh] rounded-lg shadow-2xl flex flex-col overflow-hidden animate-fade-in">
        <div className="p-4 border-b border-gray-200 flex justify-between items-center bg-gray-50">
          <div>
            <h2 className="text-xl font-bold text-gray-800">{report.title}</h2>
            <span className="text-sm text-gray-500">
              {new Date(report.date).toLocaleString()}
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-700 text-2xl font-bold px-2"
          >
            &times;
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 bg-gray-100">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-6">
              <div className="bg-white p-4 rounded shadow-sm border border-gray-200">
                <h3 className="font-bold text-gray-700 mb-2 border-b pb-1">
                  📄 Originaler Sachverhalt
                </h3>
                <div className="whitespace-pre-wrap text-sm text-gray-600 max-h-60 overflow-y-auto bg-gray-50 p-2 rounded border">
                  {report.full_text}
                </div>
              </div>

              <div className="bg-white p-4 rounded shadow-sm border border-gray-200">
                <h3 className="font-bold text-gray-700 mb-2 border-b pb-1">
                  Erkannte Fakten
                </h3>
                {result_data?.facts &&
                Object.keys(result_data.facts).length > 0 ? (
                  <ul className="space-y-2 text-sm">
                    {Object.entries(result_data.facts).map(
                      ([key, val], idx) => (
                        <li
                          key={idx}
                          className="flex justify-between border-b border-gray-100 pb-1"
                        >
                          <span className="font-medium text-gray-600">
                            {key}:
                          </span>
                          <span className="text-gray-800 text-right">
                            {val}
                          </span>
                        </li>
                      )
                    )}
                  </ul>
                ) : (
                  <p className="text-gray-400 text-sm">
                    Keine Fakten gespeichert.
                  </p>
                )}
              </div>
            </div>

            <div className="space-y-6">
              <div className="bg-white p-4 rounded shadow-sm border border-gray-200">
                <h3 className="font-bold text-gray-700 mb-2 border-b pb-1">
                  🔍 Klassifikation
                </h3>
                <div className="flex flex-wrap gap-2">
                  {result_data?.classification?.length > 0 ? (
                    result_data.classification.map((c, i) => (
                      <span
                        key={i}
                        className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-semibold"
                      >
                        {c}
                      </span>
                    ))
                  ) : (
                    <span className="text-gray-400 text-sm">
                      Keine Klassifikation
                    </span>
                  )}
                </div>
              </div>

              {finalText && (
                <div className="bg-white p-4 rounded shadow-lg border-l-4 border-blue-500">
                  <h3 className="font-bold text-gray-800 mb-2">
                    ✨ Generierter Polizeibericht
                  </h3>
                  <div className="whitespace-pre-wrap text-sm font-serif leading-relaxed text-gray-800 bg-gray-50 p-3 rounded border">
                    {finalText}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="p-4 border-t border-gray-200 bg-white flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded text-gray-600 hover:bg-gray-100 font-medium"
          >
            Schließen
          </button>
          <button
            onClick={() => onRestore(report)}
            className="px-4 py-2 rounded bg-blue-600 text-white font-bold hover:bg-blue-700 shadow-md"
          >
            In Editor übernehmen
          </button>
        </div>
      </div>
    </div>
  );
}
