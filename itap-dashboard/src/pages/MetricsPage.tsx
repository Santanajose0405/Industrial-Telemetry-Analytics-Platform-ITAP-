import {
    CartesianGrid,
    Line,
    LineChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";

const MOCK_DATA = [
    { time: "01:00", rate: 0.03 },
    { time: "02:00", rate: 0.04 },
    { time: "03:00", rate: 0.025 },
    { time: "04:00", rate: 0.06 },
    { time: "05:00", rate: 0.055 },
];

const anomalyRateFormatter = (value: number | string | undefined) => {
    const n =
        typeof value === "number"
            ? value
            : Number(value ?? 0);
    return `${(n * 100).toFixed(1)}%`;
};

export default function MetricsPage() {
    return (
        <div className="p-6 space-y-4">
            <header className="border-b pb-3">
                <h1 className="text-2xl font-semibold text-slate-900">Metrics</h1>
                <p className="mt-1 text-sm text-slate-500">
                    Pipeline-level metrics such as anomaly rate over time. Currently using
                    mock data; can be wired to metrics.json later.
                </p>
            </header>

            <section className="rounded-xl border bg-white p-4 shadow-sm">
                <h2 className="mb-3 text-sm font-semibold text-slate-800">
                    Anomaly rate (mock)
                </h2>
                <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={MOCK_DATA}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} />
                            <XAxis dataKey="time" />
                            <YAxis
                                tickFormatter={(v) => `${(Number(v) * 100).toFixed(0)}%`}
                            />
                            <Tooltip formatter={anomalyRateFormatter} />
                            <Line
                                type="monotone"
                                dataKey="rate"
                                strokeWidth={2}
                                dot={false}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </section>
        </div>
    );
}
