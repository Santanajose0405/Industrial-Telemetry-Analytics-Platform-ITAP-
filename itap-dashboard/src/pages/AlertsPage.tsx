// src/pages/AlertsPage.tsx

type MockAlert = {
    id: string;
    timestamp: string;
    device_id: string;
    severity: "INFO" | "WARNING" | "CRITICAL";
    route: string;
    message: string;
};

const MOCK_ALERTS: MockAlert[] = [
    {
        id: "1",
        timestamp: "2026-01-15T02:15:05Z",
        device_id: "PUMP-001",
        severity: "CRITICAL",
        route: "maintenance",
        message: "Bearing wear exceeds threshold",
    },
    {
        id: "2",
        timestamp: "2026-01-15T02:10:00Z",
        device_id: "PUMP-002",
        severity: "WARNING",
        route: "thermal",
        message: "Outlet temperature trending high",
    },
];

export default function AlertsPage() {
    return (
        <div className="space-y-4 p-6">
            <div className="flex flex-col gap-1">
                <h1 className="text-2xl font-semibold text-slate-900">Alerts</h1>
                <p className="text-sm text-slate-600">
                    Recent anomaly alerts. This view can be wired to alerts.json later.
                </p>
            </div>

            <div className="rounded-xl border bg-white p-4 shadow-sm">
                <div className="mb-3 text-sm font-medium text-slate-700">
                    Latest alerts (mock data)
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full min-w-[640px] text-left text-sm">
                        <thead>
                            <tr className="border-b text-xs uppercase text-slate-500">
                                <th className="py-2 pr-4">Time (UTC)</th>
                                <th className="py-2 pr-4">Device</th>
                                <th className="py-2 pr-4">Severity</th>
                                <th className="py-2 pr-4">Route</th>
                                <th className="py-2 pr-4">Message</th>
                            </tr>
                        </thead>
                        <tbody>
                            {MOCK_ALERTS.map((a) => (
                                <tr key={a.id} className="border-b last:border-0">
                                    <td className="py-2 pr-4 text-xs text-slate-700">
                                        {a.timestamp}
                                    </td>
                                    <td className="py-2 pr-4 text-xs text-slate-800">
                                        {a.device_id}
                                    </td>
                                    <td className="py-2 pr-4">
                                        <span
                                            className={
                                                "inline-flex rounded-full px-2 py-0.5 text-[11px] font-semibold " +
                                                (a.severity === "CRITICAL"
                                                    ? "bg-rose-50 text-rose-700"
                                                    : a.severity === "WARNING"
                                                        ? "bg-amber-50 text-amber-700"
                                                        : "bg-sky-50 text-sky-700")
                                            }
                                        >
                                            {a.severity}
                                        </span>
                                    </td>
                                    <td className="py-2 pr-4 text-xs text-slate-700">
                                        {a.route}
                                    </td>
                                    <td className="py-2 pr-4 text-xs text-slate-800">
                                        {a.message}
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
