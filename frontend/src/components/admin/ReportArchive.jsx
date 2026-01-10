import { useState, useEffect } from "react";
import { createPortal } from "react-dom";

export default function ReportArchive() {
    const [reports, setReports] = useState([]);
    const [loading, setLoading] = useState(false);
    const [offset, setOffset] = useState(0);
    const [hasMore, setHasMore] = useState(true);
    const [selectedIds, setSelectedIds] = useState([]);

    const LIMIT = 20;

    // Daten laden
    const fetchReports = async (currentOffset) => {
        if (loading) return;
        setLoading(true);

        try {
            const res = await fetch(`http://localhost:8000/api/reports/history?limit=${LIMIT}&skip=${currentOffset}`);
            if (!res.ok) throw new Error("Fehler beim Laden");
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

    return (
        <>
            {/* Haupt-Container */}
            <div className="space-y-6 relative pb-24">
                
                {/* Header */}
                <div className="flex justify-between items-center border-b border-gray-200 pb-4">
                    <div>
                        <h2 className="text-xl font-bold text-gray-800">Archiv & Tests</h2>
                        <p className="text-sm text-gray-500">Historische Berichte auswählen und vergleichen.</p>
                    </div>
                    <span className="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded-full border border-gray-200">
                        {reports.length} geladen
                    </span>
                </div>

                {/* Grid Liste */}
                <div className="grid gap-4">
                    {reports.map((report) => {
                        const isSelected = selectedIds.includes(report.id);
                        return (
                            <div
                                key={report.id}
                                onClick={() => toggleSelection(report.id)}
                                className={`
                                    group relative p-4 rounded-lg border cursor-pointer transition-all duration-200 bg-white
                                    ${isSelected
                                        ? 'border-purple-500 shadow-md ring-1 ring-purple-500 bg-purple-50'
                                        : 'border-gray-200 hover:shadow-md hover:border-gray-300'
                                    }
                                `}
                            >
                                <div className="flex justify-between items-start gap-4">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-1">
                                            <h3 className="font-bold text-gray-800">{report.title}</h3>
                                            <span className="text-xs text-gray-400 font-mono">
                                                {new Date(report.date).toLocaleDateString()} • {new Date(report.date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                            </span>
                                        </div>
                                        <p className="text-gray-600 text-sm line-clamp-2">
                                            {report.preview || "Keine Vorschau..."}
                                        </p>

                                        {/* Tags */}
                                        {report.result_data?.classification?.length > 0 && (
                                            <div className="mt-2 flex gap-1 flex-wrap">
                                                {report.result_data.classification.map((tag, idx) => (
                                                    <span key={idx} className="text-[10px] uppercase font-bold bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded border border-gray-200">
                                                        {tag}
                                                    </span>
                                                ))}
                                            </div>
                                        )}
                                    </div>

                                    {/* Checkbox */}
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

                {/* Load More Button */}
                {hasMore && (
                    <div className="text-center pt-4">
                        <button
                            onClick={loadMore}
                            disabled={loading}
                            className="text-sm text-gray-500 hover:text-gray-800 font-medium underline decoration-dotted transition-colors"
                        >
                            {loading ? "Lade..." : "Ältere Berichte laden"}
                        </button>
                    </div>
                )}
            </div>

            { }
            {selectedIds.length > 0 && createPortal(
                <div 
                    style={{
                        position: 'fixed',
                        bottom: '2rem',
                        left: '50%',
                        transform: 'translateX(-50%)',
                        zIndex: 2147483647,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '1rem',
                        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)'
                    }}
                    className="bg-gray-900 text-white px-6 py-3 rounded-full border border-gray-700"
                >
                    <span className="font-bold text-sm whitespace-nowrap">{selectedIds.length} ausgewählt</span>
                    <div className="h-4 w-px bg-gray-600"></div>

                    <button
                        className="bg-purple-600 hover:bg-purple-500 text-white px-4 py-1.5 rounded-full font-bold text-sm shadow-lg whitespace-nowrap"
                        onClick={() => alert(`Starte Vergleich-Logik für IDs: ${selectedIds.join(", ")}`)}
                    >
                        Vergleich starten
                    </button>

                    <button
                        onClick={(e) => { e.stopPropagation(); setSelectedIds([]) }}
                        className="text-gray-400 hover:text-white ml-2 text-sm font-medium hover:underline whitespace-nowrap"
                    >
                        Abbrechen
                    </button>
                </div>,
                document.body
            )}
        </>
    );
}