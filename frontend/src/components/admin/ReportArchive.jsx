import { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import EvaluationModal from "./EvaluationModal";

export default function ReportArchive() {
    const [reports, setReports] = useState([]);
    const [loading, setLoading] = useState(false);
    const [offset, setOffset] = useState(0);
    const [hasMore, setHasMore] = useState(true);
    const [selectedIds, setSelectedIds] = useState([]);

    // Modal State
    const [showEvalModal, setShowEvalModal] = useState(false);
    const [evalData, setEvalData] = useState(null);
    const [evalLoading, setEvalLoading] = useState(false);

    const LIMIT = 20;

    const fetchReports = async (currentOffset) => {
        if (loading) return;
        setLoading(true);
        try {
            const res = await fetch(`http://localhost:8000/api/reports/history?limit=${LIMIT}&skip=${currentOffset}`);
            if (!res.ok) throw new Error("Fetch error");
            const data = await res.json();

            if (data.length < LIMIT) setHasMore(false);
            setReports((prev) => (currentOffset === 0 ? data : [...prev, ...data]));
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchReports(0);
    }, []);

    const loadMore = () => {
        const newOffset = offset + LIMIT;
        setOffset(newOffset);
        fetchReports(newOffset);
    };

    const toggleSelection = (id) => {
        setSelectedIds((prev) =>
            prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
        );
    };

    const toggleReference = async (e, report) => {
        e.stopPropagation();

        try {
            const res = await fetch(`http://localhost:8000/api/eval/set-reference/${report.id}`, { method: "POST" });
            if (res.ok) {
                const data = await res.json();

                setReports(prev => prev.map(r =>
                    r.id === report.id ? { ...r, is_reference: data.is_reference } : r
                ));
            } else {
                alert("Fehler: Konnte Status nicht ändern.");
            }
        } catch (err) {
            alert("Netzwerkfehler.");
        }
    };

    const startComparison = async () => {
        if (selectedIds.length !== 2) {
            alert("Bitte wähle genau ZWEI Berichte aus.");
            return;
        }

        setShowEvalModal(true);
        setEvalLoading(true);

        const [id1, id2] = selectedIds;

        const r1 = reports.find(r => r.id === id1);
        const r2 = reports.find(r => r.id === id2);

        // --- SMART SWAP ---
        let candidateId, referenceId;

        if (r1.is_reference && !r2.is_reference) {
            referenceId = r1.id;
            candidateId = r2.id;
        } else if (r2.is_reference && !r1.is_reference) {
            referenceId = r2.id;
            candidateId = r1.id;
        } else {
            candidateId = id1;
            referenceId = id2;
        }

        try {
            const res = await fetch("http://localhost:8000/api/eval/compare", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    candidate_id: candidateId,
                    reference_id: referenceId
                })
            });

            if (!res.ok) throw new Error("Comparison failed");

            const data = await res.json();
            setEvalData(data);
        } catch (err) {
            console.error(err);
            alert("Fehler beim Vergleich.");
            setShowEvalModal(false);
        } finally {
            setEvalLoading(false);
        }
    };

    return (
        <>
            <div className="space-y-6 relative pb-24">
                <div className="flex justify-between items-center border-b border-gray-200 pb-4">
                    <div>
                        <h2 className="text-xl font-bold text-gray-800">Archiv & Tests</h2>
                        <p className="text-sm text-gray-500">Historische Berichte verwalten und evaluieren.</p>
                    </div>
                    <span className="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded-full border border-gray-200">
                        {reports.length} geladen
                    </span>
                </div>

                <div className="grid gap-4">
                    {reports.map((report) => {
                        const isSelected = selectedIds.includes(report.id);
                        const isRef = report.is_reference;

                        return (
                            <div
                                key={report.id}
                                onClick={() => toggleSelection(report.id)}
                                className={`
                                    group relative p-4 rounded-lg border cursor-pointer transition-all duration-200 bg-white
                                    ${isSelected
                                        ? 'border-purple-500 shadow-md ring-1 ring-purple-500 bg-purple-50'
                                        : isRef
                                            ? 'border-yellow-400 shadow-sm bg-yellow-50/30'
                                            : 'border-gray-200 hover:shadow-md hover:border-gray-300'
                                    }
                                `}
                            >
                                <div className="flex justify-between items-start gap-4">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-1">
                                            <h3 className="font-bold text-gray-800">{report.title}</h3>

                                            {isRef && (
                                                <span className="text-[10px] uppercase font-bold bg-yellow-100 text-yellow-700 px-1.5 py-0.5 rounded border border-yellow-200 flex items-center gap-1">
                                                    ★ Golden Truth
                                                </span>
                                            )}

                                            <span className="text-xs text-gray-400 font-mono ml-auto md:ml-0">
                                                {new Date(report.created_at || report.date).toLocaleDateString()}
                                            </span>
                                        </div>
                                        <p className="text-gray-600 text-sm line-clamp-2">
                                            {report.preview || (report.body_md ? JSON.parse(report.body_md)?.data?.text?.substring(0, 100) : "...")}
                                        </p>

                                        { }
                                        <div className="mt-3 flex gap-2">
                                            <button
                                                onClick={(e) => toggleReference(e, report)}
                                                className={`text-xs z-10 hover:underline flex items-center gap-1 font-medium
                                                    ${isRef
                                                        ? "text-red-500 hover:text-red-700"
                                                        : "text-gray-400 hover:text-yellow-600"
                                                    }
                                                `}
                                            >
                                                {isRef ? "✖ Nicht mehr als Referenz speichern" : "☆ Als Referenz festlegen"}
                                            </button>
                                        </div>
                                        { }

                                    </div>

                                    <div className={`
                                        w-6 h-6 rounded border flex items-center justify-center transition-colors mt-1 flex-shrink-0
                                        ${isSelected ? 'bg-purple-600 border-purple-600' : 'border-gray-300 group-hover:border-gray-400'}
                                    `}>
                                        {isSelected && <span className="text-white text-sm font-bold">✓</span>}
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>

                {hasMore && (
                    <div className="text-center pt-4">
                        <button onClick={loadMore} disabled={loading} className="text-sm text-gray-500 hover:text-gray-800 underline">
                            {loading ? "Lade..." : "Ältere Berichte laden"}
                        </button>
                    </div>
                )}
            </div>

            {/* Floating Action Bar */}
            {selectedIds.length > 0 && createPortal(
                <div
                    style={{
                        position: 'fixed', bottom: '2rem', left: '50%', transform: 'translateX(-50%)', zIndex: 50,
                        display: 'flex', alignItems: 'center', gap: '1rem',
                        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)'
                    }}
                    className="bg-gray-900 text-white px-6 py-3 rounded-full border border-gray-700"
                >
                    <span className="font-bold text-sm whitespace-nowrap">{selectedIds.length} ausgewählt</span>
                    <div className="h-4 w-px bg-gray-600"></div>

                    {(() => {
                        const r1 = reports.find(r => r.id === selectedIds[0]);
                        const r2 = reports.find(r => r.id === selectedIds[1]);

                        // selected = is_reference===true?
                        const hasReference = r1?.is_reference || r2?.is_reference;

                        const isReady = selectedIds.length === 2 && hasReference;

                        return (
                            <div className="flex items-center gap-3">
                                <button
                                    className={`px-4 py-1.5 rounded-full font-bold text-sm shadow-lg whitespace-nowrap transition-colors
                                        ${isReady
                                            ? 'bg-purple-600 hover:bg-purple-500 text-white'
                                            : 'bg-gray-700 text-gray-400 cursor-not-allowed'}`
                                    }
                                    onClick={startComparison}
                                    disabled={!isReady}
                                >
                                    Vergleich starten
                                </button>

                                {/* Warning */}
                                {selectedIds.length === 2 && !hasReference && (
                                    <span className="text-xs text-red-300 font-medium animate-pulse">
                                        ⚠ Mind. 1 Referenz nötig!
                                    </span>
                                )}
                            </div>
                        );
                    })()}

                    <button
                        onClick={(e) => { e.stopPropagation(); setSelectedIds([]) }}
                        className="text-gray-400 hover:text-white ml-2 text-sm font-medium hover:underline whitespace-nowrap"
                    >
                        Abbrechen
                    </button>
                </div>,
                document.body
            )}

            <EvaluationModal
                show={showEvalModal}
                onClose={() => setShowEvalModal(false)}
                comparisonData={evalData}
                loading={evalLoading}
            />
        </>
    );
}