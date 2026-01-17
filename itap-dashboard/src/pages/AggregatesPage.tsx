// src/pages/AggregatePage.tsx

type MockAggregate = {
    bucket: string;
    devices: number;
    alerts: number;
    avg_severity: number;
};

const MOCK_AGGREGATES: MockAggregate[] = [
    { bucket: "Last 1h", devices: 42, alerts: 7, avg_severity: 2.3 },
    { bucket: "Last 24h", devices: 58, alerts: 23, avg_severity: 1.8 },
];

export default function AggregatePage() {
    return (
        <div className="space-y-4 p-6">
            <div className="flex flex-col gap-1">
                <h1 className="text-2xl font-semibold text-slate-900">
                    Fleet aggregates
                </h1>
                <p className="text-sm text-slate-600">
                    Time-bucketed aggregates (alerts per device, average severity, etc).
                    This view can later bind to aggregate_summaries.json.
                </p>
            </div>

            <div className="rounded-xl border bg-white p-4 shadow-sm">
                <div className="mb-3 text-sm font-medium text-slate-700">
                    Aggregate summaries (mock data)
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full min-w-[560px] text-left text-sm">
                        <thead>
                            <tr className="border-b text-xs uppercase text-slate-500">
                                <th className="py-2 pr-4">Bucket</th>
                                <th className="py-2 pr-4">Devices</th>
                                <th className="py-2 pr-4">Alerts</th>
                                <th className="py-2 pr-4">Avg severity</th>
                            </tr>
                        </thead>
                        <tbody>
                            {MOCK_AGGREGATES.map((row) => (
                                <tr key={row.bucket} className="border-b last:border-0">
                                    <td className="py-2 pr-4 text-xs text-slate-800">
                                        {row.bucket}
                                    </td>
                                    <td className="py-2 pr-4 text-xs text-slate-800">
                                        {row.devices}
                                    </td>
                                    <td className="py-2 pr-4 text-xs text-slate-800">
                                        {row.alerts}
                                    </td>
                                    <td className="py-2 pr-4 text-xs text-slate-800">
                                        {row.avg_severity.toFixed(2)}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
