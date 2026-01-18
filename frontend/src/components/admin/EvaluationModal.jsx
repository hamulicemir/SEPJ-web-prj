import {
    Modal,
    ModalHeader,
    ModalBody,
    ModalFooter,
    Button,
    Spinner,
} from "flowbite-react";

import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Radar,
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
} from "recharts";

export default function EvaluationModal({
    show,
    onClose,
    comparisonData,
    loading,
}) {
    if (!show) return null;

    return (
        <Modal show={show} onClose={onClose} size="7xl">
            <ModalHeader>Bericht-Evaluierung</ModalHeader>

            <ModalBody>
                {loading ? (
                    <div className="flex justify-center p-10">
                        <Spinner size="xl" aria-label="Lade Metriken..." />
                    </div>
                ) : comparisonData ? (
                    <div className="space-y-8">
                        {/* KPI Kacheln */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
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
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 h-[500px]">
                            {/* Chart 1: Bar chart */}
                            <div className="bg-gray-50 p-6 rounded-lg border flex flex-col">
                                <h4 className="text-base font-bold text-gray-700 mb-6 text-center">
                                    Metriken Übersicht
                                </h4>

                                <div className="flex-grow w-full min-h-0">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <BarChart
                                            data={[
                                                {
                                                    name: "Stil",
                                                    score: comparisonData.metrics.rouge_score,
                                                },
                                                {
                                                    name: "Fakten",
                                                    score: comparisonData.metrics.fact_completeness,
                                                },
                                                {
                                                    name: "Text-Nähe",
                                                    score:
                                                        comparisonData.metrics.levenshtein_similarity,
                                                },
                                            ]}
                                            margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                                        >
                                            <CartesianGrid strokeDasharray="3 3" />
                                            <XAxis dataKey="name" tick={{ fontSize: 14 }} />
                                            <YAxis domain={[0, 100]} tick={{ fontSize: 14 }} />
                                            <Tooltip
                                                contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                                cursor={{ fill: 'transparent' }}
                                            />
                                            <Bar
                                                dataKey="score"
                                                fill="#3b82f6"
                                                name="Score %"
                                                radius={[4, 4, 0, 0]}
                                                barSize={60} 
                                            />
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>

                            {/* Chart 2: Radar chart */}
                            <div className="bg-gray-50 p-6 rounded-lg border flex flex-col items-center">
                                <h4 className="text-base font-bold text-gray-700 mb-2 text-center">
                                    Qualitäts-Profil
                                </h4>

                                <div className="flex-grow w-full min-h-0">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <RadarChart
                                            cx="50%"
                                            cy="50%"
                                            outerRadius="80%"
                                            data={[
                                                {
                                                    subject: "Stil",
                                                    A: comparisonData.metrics.rouge_score,
                                                    fullMark: 100,
                                                },
                                                {
                                                    subject: "Fakten",
                                                    A: comparisonData.metrics.fact_completeness,
                                                    fullMark: 100,
                                                },
                                                {
                                                    subject: "Nähe",
                                                    A: comparisonData.metrics.levenshtein_similarity,
                                                    fullMark: 100,
                                                },
                                            ]}
                                        >
                                            <PolarGrid />
                                            <PolarAngleAxis dataKey="subject" tick={{ fontSize: 14, fontWeight: 600 }} />
                                            <PolarRadiusAxis
                                                angle={30}
                                                domain={[0, 100]}
                                            />
                                            <Radar
                                                name="Dieser Bericht"
                                                dataKey="A"
                                                stroke="#10b981"
                                                fill="#10b981"
                                                fillOpacity={0.5}
                                            />
                                            <Tooltip />
                                        </RadarChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="text-center text-gray-500 py-20 text-lg">
                        Keine Daten verfügbar.
                    </div>
                )}
            </ModalBody>

            <ModalFooter>
                <Button color="gray" onClick={onClose}>
                    Schließen
                </Button>
            </ModalFooter>
        </Modal>
    );
}

function MetricCard({ title, value, desc, color }) {
    const colors = {
        blue: "text-blue-700 bg-blue-50 border-blue-200",
        green: "text-green-700 bg-green-50 border-green-200",
        purple: "text-purple-700 bg-purple-50 border-purple-200",
    };

    return (
        <div
            className={`p-6 rounded-lg border ${colors[color] || colors.blue
                } text-center shadow-sm hover:shadow-md transition-shadow`}
        >
            <div className="text-4xl font-extrabold mb-2">{value}%</div>
            <div className="font-bold text-sm uppercase tracking-wider">
                {title}
            </div>
            <div className="text-sm opacity-80 mt-1 font-medium">{desc}</div>
        </div>
    );
}