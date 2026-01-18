import { Modal, Button, Spinner } from "flowbite-react";
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts';

export default function EvaluationModal({ show, onClose, comparisonData, loading }) {
    if (!show) return null;

    return (
        <Modal show={show} onClose={onClose} size="4xl">
            <Modal.Header>Bericht-Evaluierung</Modal.Header>
            <Modal.Body>
                {loading ? (
                    <div className="flex justify-center p-10">
                        <Spinner size="xl" aria-label="Lade Metriken..." />
                    </div>
                ) : comparisonData ? (
                    <div className="space-y-8">

                        {/* KPI Kacheln */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <MetricCard
                                title="ROUGE Score"
                                value={comparisonData.metrics.rouge_score}
                                desc="Sprachliche Ähnlichkeit (Stil)"
                                color="blue"
                            />
                            <MetricCard
                                title="Fakten-Check"
                                value={comparisonData.metrics.fact_completeness}
                                desc="Gefundene Personen & Orte"
                                color="green"
                            />
                            <MetricCard
                                title="Levenshtein"
                                value={comparisonData.metrics.levenshtein_similarity}
                                desc="Zeichen-Übereinstimmung"
                                color="purple"
                            />
                        </div>

                        {/* Charts Area */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 h-80">

                            {/* Chart 1: Bar chart */}
                            <div className="bg-gray-50 p-4 rounded-lg border">
                                <h4 className="text-sm font-bold text-gray-500 mb-4 text-center">Metriken Übersicht</h4>
                                <ResponsiveContainer width="100%" height="80%">
                                    <BarChart
                                        data={[
                                            { name: 'Stil', score: comparisonData.metrics.rouge_score },
                                            { name: 'Fakten', score: comparisonData.metrics.fact_completeness },
                                            { name: 'Text-Nähe', score: comparisonData.metrics.levenshtein_similarity },
                                        ]}
                                    >
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="name" />
                                        <YAxis domain={[0, 100]} />
                                        <Tooltip />
                                        <Bar dataKey="score" fill="#8884d8" name="Score %" radius={[4, 4, 0, 0]} />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>

                            {/* Chart 2: Radar chart */}
                            <div className="bg-gray-50 p-4 rounded-lg border flex flex-col items-center">
                                <h4 className="text-sm font-bold text-gray-500 mb-2 text-center">Qualitäts-Profil</h4>
                                <div className="flex-grow w-full">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <RadarChart cx="50%" cy="50%" outerRadius="70%" data={[
                                            { subject: 'Stil', A: comparisonData.metrics.rouge_score, fullMark: 100 },
                                            { subject: 'Fakten', A: comparisonData.metrics.fact_completeness, fullMark: 100 },
                                            { subject: 'Nähe', A: comparisonData.metrics.levenshtein_similarity, fullMark: 100 },
                                        ]}>
                                            <PolarGrid />
                                            <PolarAngleAxis dataKey="subject" />
                                            <PolarRadiusAxis angle={30} domain={[0, 100]} />
                                            <Radar name="Dieser Bericht" dataKey="A" stroke="#82ca9d" fill="#82ca9d" fillOpacity={0.6} />
                                            <Tooltip />
                                        </RadarChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>

                        </div>
                    </div>
                ) : (
                    <div className="text-center text-gray-500">Keine Daten verfügbar.</div>
                )}
            </Modal.Body>
            <Modal.Footer>
                <Button color="gray" onClick={onClose}>Schließen</Button>
            </Modal.Footer>
        </Modal>
    );
}

function MetricCard({ title, value, desc, color }) {
    const colors = {
        blue: "text-blue-600 bg-blue-50 border-blue-200",
        green: "text-green-600 bg-green-50 border-green-200",
        purple: "text-purple-600 bg-purple-50 border-purple-200",
    }
    return (
        <div className={`p-4 rounded-lg border ${colors[color] || colors.blue} text-center`}>
            <div className="text-3xl font-bold">{value}%</div>
            <div className="font-semibold text-sm uppercase tracking-wide mt-1">{title}</div>
            <div className="text-xs opacity-75 mt-1">{desc}</div>
        </div>
    )
}