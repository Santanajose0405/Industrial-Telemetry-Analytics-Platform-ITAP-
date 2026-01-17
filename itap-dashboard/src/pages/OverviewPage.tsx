// src/pages/OverviewPage.tsx
import { useQuery } from "@tanstack/react-query";
import { fetchJson } from "@/lib/api/client";
import { HealthSchema, type Health } from "@/lib/schemas/health";

export default function OverviewPage() {
    const q = useQuery<Health>({
        queryKey: ["overview", "health"],
        queryFn: () => fetchJson("/api/health", HealthSchema),
        refetchInterval: 30_000, // refresh every 30s
    });

    if (q.isLoading) {
        return <div className="p-6 text-slate-700">Loading overview…</div>;
    }

    if (q.isError || !q.data) {
        return (
            <div className="p-6 text-red-700">
                Overview error: {String(q.error ?? "No data")}
            </div>
        );
    }

    const data = q.data;
    const totalArtifacts = Object.keys(data.artifacts_present).length;
    const presentArtifacts = Object.values(data.artifacts_present).filter(Boolean)
        .length;
    const missingArtifacts = totalArtifacts - presentArtifacts;

    return (
        <div className="space-y-6 p-6">
            {/* Header */}
            <div className="flex flex-col gap-1">
                <h1 className="text-2xl font-semibold text-slate-900">
                    ITAP Dashboard
                </h1>
                <p className="text-sm text-slate-600">
                    High-level status of the anomaly detection pipeline.
                </p>
            </div>

            {/* KPIs */}
            <div className="grid gap-4 md:grid-cols-3">
                {/* Overall status */}
                <div className="rounded-xl border bg-white p-4 shadow-sm">
                    <div className="text-xs font-medium uppercase text-slate-500">
                        Overall status
                    </div>
                    <div
                        className={
                            "mt-1 inline-flex items-center rounded-full px-3 py-1 text-sm font-semibold " +
                            (data.status === "ok"
                                ? "bg-emerald-50 text-emerald-700"
                                : "bg-amber-50 text-amber-700")
                        }
                    >
                        {data.status === "ok" ? "Healthy" : data.status}
                    </div>
                    <p className="mt-2 text-xs text-slate-500">
                        Based on artifact presence and basic API health.
                    </p>
                </div>

                {/* Artifacts present */}
                <div className="rounded-xl border bg-white p-4 shadow-sm">
                    <div className="text-xs font-medium uppercase text-slate-500">
                        Artifacts present
                    </div>
                    <div className="mt-1 text-2xl font-semibold text-slate-900">
                        {presentArtifacts}{" "}
                        <span className="text-base text-slate-500">/ {totalArtifacts}</span>
                    </div>
                    <p className="mt-2 text-xs text-slate-500">
                        JSON outputs available for the latest pipeline run.
                    </p>
                </div>

                {/* Missing artifacts (if any) */}
                <div className="rounded-xl border bg-white p-4 shadow-sm">
                    <div className="text-xs font-medium uppercase text-slate-500">
                        Missing artifacts
                    </div>
                    <div
                        className={
                            "mt-1 text-2xl font-semibold " +
                            (missingArtifacts === 0 ? "text-emerald-700" : "text-rose-700")
                        }
                    >
                        {missingArtifacts}
                    </div>
                    <p className="mt-2 text-xs text-slate-500">
                        Any non-zero value here means part of the pipeline didn&apos;t
                        write outputs.
                    </p>
                </div>
            </div>

            {/* Artifact list (simple table) */}
            <div className="rounded-xl border bg-white p-4 shadow-sm">
                <div className="mb-3 text-sm font-medium text-slate-700">
                    Artifact overview
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full min-w-[480px] text-left text-sm">
                        <thead>
                            <tr className="border-b text-xs uppercase text-slate-500">
                                <th className="py-2 pr-4">File</th>
                                <th className="py-2 pr-4">Present</th>
                            </tr>
                        </thead>
                        <tbody>
                            {Object.entries(data.artifacts_present).map(([file, ok]) => (
                                <tr key={file} className="border-b last:border-0">
                                    <td className="py-2 pr-4 font-mono text-xs text-slate-800">
                                        {file}
                                    </td>
                                    <td className="py-2 pr-4">
                                        <span
                                            className={
                                                "inline-flex rounded-full px-2 py-0.5 text-[11px] font-semibold " +
                                                (ok
                                                    ? "bg-emerald-50 text-emerald-700"
                                                    : "bg-rose-50 text-rose-700")
                                            }
                                        >
                                            {ok ? "Present" : "Missing"}
                                        </span>
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
