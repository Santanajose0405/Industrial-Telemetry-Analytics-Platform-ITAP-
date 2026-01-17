// src/pages/HealthPage.tsx
import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchJson } from "@/lib/api/client";
import { HealthSchema, type Health } from "@/lib/schemas/health";

// Fallback "now" captured once at module load (not during render)
const FALLBACK_NOW_MS = Date.now();

type HealthDiagnostics = {
    status: string;
    artifact_dir: string;
    artifacts_present: Record<string, boolean>;
    artifacts_mtime_utc: Record<string, string | null | undefined>;
    overview: {
        present: number;
        missing: number;
        total: number;
        maxAgeMinutes: number | null;
        lastScoreRunUtc: string | null;
    };
};

// Freshness SLAs per artifact (ms)
const SLA_MS: Record<string, number> = {
    "alerts.json": 5 * 60 * 1000, // 5 minutes
    "metrics.json": 60 * 60 * 1000, // 1 hour
    "aggregate_summaries.json": 10 * 60 * 1000,
    "explanations_top.json": 10 * 60 * 1000,
};

const DEFAULT_SLA_MS = 30 * 60 * 1000; // 30 minutes

function parseIsoOrNull(v: string | undefined | null): Date | null {
    if (!v) return null;
    const t = Date.parse(v);
    return Number.isNaN(t) ? null : new Date(t);
}

/**
 * Compute summary stats from the raw /api/health payload.
 * nowMs is passed in so this stays pure and testable.
 */
function summarizeHealth(data: Health, nowMs: number) {
    const entries = Object.entries(data.artifacts_present);

    let present = 0;
    let missing = 0;

    for (const [, ok] of entries) {
        if (ok) present += 1;
        else missing += 1;
    }

    const total = present + missing;

    const ages: number[] = [];
    for (const [file] of entries) {
        const mtime = data.artifacts_mtime_utc?.[file];
        const dt = parseIsoOrNull(mtime);
        if (dt) {
            ages.push(nowMs - dt.getTime());
        }
    }

    const maxAgeMs = ages.length ? Math.max(...ages) : null;

    const lastScoreRunStr =
        data.artifacts_mtime_utc?.["alerts.json"] ??
        data.artifacts_mtime_utc?.["metrics.json"] ??
        null;
    const lastScoreRun = parseIsoOrNull(lastScoreRunStr);

    return {
        present,
        missing,
        total,
        maxAgeMs,
        entries,
        lastScoreRun,
    };
}

/**
 * Build the diagnostics payload we copy to the clipboard.
 */
function buildDiagnostics(
    data: Health,
    summary: ReturnType<typeof summarizeHealth>,
): HealthDiagnostics {
    const maxAgeMinutes =
        summary.maxAgeMs !== null ? Math.round(summary.maxAgeMs / 60000) : null;

    return {
        status: data.status,
        artifact_dir: data.artifact_dir,
        artifacts_present: data.artifacts_present,
        artifacts_mtime_utc: data.artifacts_mtime_utc,
        overview: {
            present: summary.present,
            missing: summary.missing,
            total: summary.total,
            maxAgeMinutes,
            lastScoreRunUtc: summary.lastScoreRun
                ? summary.lastScoreRun.toISOString()
                : null,
        },
    };
}

export default function HealthPage() {
    // 1. Fetch health once per poll
    const q = useQuery({
        queryKey: ["health"],
        queryFn: () => fetchJson("/api/health", HealthSchema),
        refetchInterval: 10_000,
    });

    // 2. Derive summary stats from the data (always called, hooks-safe)
    //    We use React Query's dataUpdatedAt as our "now" reference.
    const summary = useMemo(
        () =>
            q.data
                ? summarizeHealth(
                    q.data,
                    q.dataUpdatedAt ?? FALLBACK_NOW_MS,
                )
                : null,
        [q.data, q.dataUpdatedAt],
    );

    // 3. Early render branches (no hooks below this point)
    if (q.isLoading) return <div className="p-6">Loading health…</div>;
    if (q.isError || !q.data || !summary) {
        return (
            <div className="p-6 text-red-600">
                Health error: {String(q.error ?? "No data")}
            </div>
        );
    }

    const { present, missing, total, entries, lastScoreRun } = summary;

    const overallStatus =
        q.data.status === "ok" && missing === 0 ? "Healthy" : "Attention";
    const overallStatusClass =
        overallStatus === "Healthy" ? "text-emerald-600" : "text-amber-600";

    const nowMs = q.dataUpdatedAt ?? FALLBACK_NOW_MS;

    return (
        <div className="p-8 space-y-8">
            <header className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
                <div className="space-y-1">
                    <h1 className="text-2xl font-semibold text-slate-900">
                        ITAP Dashboard
                    </h1>
                    <p className="text-sm text-slate-500">
                        High-level status of the anomaly detection pipeline.
                    </p>
                </div>

                <button
                    type="button"
                    onClick={async () => {
                        const diagnostics = buildDiagnostics(q.data, summary);
                        const text = JSON.stringify(diagnostics, null, 2);

                        try {
                            await navigator.clipboard.writeText(text);
                        } catch {
                            // Fallback: open as a new window if clipboard is blocked
                            const blob = new Blob([text], {
                                type: "application/json",
                            });
                            const url = URL.createObjectURL(blob);
                            window.open(url, "_blank");
                        }
                    }}
                    className="inline-flex items-center rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 shadow-sm hover:bg-slate-50"
                >
                    Copy diagnostics JSON
                </button>
            </header>

            {/* KPI cards */}
            <section className="grid gap-6 md:grid-cols-3">
                {/* Overall status */}
                <div className="rounded-xl border bg-white p-5 shadow-sm">
                    <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                        Overall status
                    </div>
                    <div className={`mt-3 text-xl font-semibold ${overallStatusClass}`}>
                        {overallStatus}
                    </div>
                    <p className="mt-2 text-xs text-slate-500">
                        Based on artifact presence and basic API health.
                    </p>
                </div>

                {/* Artifacts present */}
                <div className="rounded-xl border bg-white p-5 shadow-sm">
                    <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                        Artifacts present
                    </div>
                    <div className="mt-3 flex items-baseline gap-1">
                        <span className="text-2xl font-semibold text-slate-900">
                            {present}
                        </span>
                        <span className="text-sm text-slate-400">/ {total}</span>
                    </div>
                    <p className="mt-2 text-xs text-slate-500">
                        JSON outputs available for the latest pipeline run.
                    </p>
                </div>

                {/* Missing artifacts */}
                <div className="rounded-xl border bg-white p-5 shadow-sm">
                    <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                        Missing artifacts
                    </div>
                    <div className="mt-3 text-2xl font-semibold text-slate-900">
                        {missing}
                    </div>
                    <p className="mt-2 text-xs text-slate-500">
                        Any non-zero value here means part of the pipeline didn&apos;t
                        write outputs.
                    </p>
                </div>
            </section>

            {/* Artifact table */}
            <section className="space-y-3">
                <h2 className="text-sm font-semibold text-slate-900">
                    Artifact overview
                </h2>

                <div className="overflow-hidden rounded-xl border bg-white shadow-sm">
                    <table className="min-w-full text-left text-sm">
                        <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
                            <tr>
                                <th className="px-4 py-2">File</th>
                                <th className="px-4 py-2">Last updated (UTC)</th>
                                <th className="px-4 py-2">Age</th>
                                <th className="px-4 py-2">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {entries.map(([file, ok]) => {
                                const mtime = q.data.artifacts_mtime_utc?.[file];
                                const dt = parseIsoOrNull(mtime);
                                const ageMs = dt ? nowMs - dt.getTime() : null;

                                const slaMs = SLA_MS[file] ?? DEFAULT_SLA_MS;
                                const isStale = ageMs !== null && ageMs > slaMs;

                                const state = !ok
                                    ? "MISSING"
                                    : isStale
                                        ? "STALE"
                                        : "OK";

                                const stateClass =
                                    state === "OK"
                                        ? "text-emerald-600"
                                        : state === "STALE"
                                            ? "text-amber-600"
                                            : "text-rose-600";

                                return (
                                    <tr key={file}>
                                        <td className="px-4 py-2 font-mono text-xs text-slate-800">
                                            {file}
                                        </td>
                                        <td className="px-4 py-2 text-xs text-slate-600">
                                            {dt ? dt.toISOString() : "—"}
                                        </td>
                                        <td className="px-4 py-2 text-xs text-slate-600">
                                            {ageMs !== null
                                                ? `${Math.round(ageMs / 60000)} min`
                                                : "—"}
                                        </td>
                                        <td
                                            className={`px-4 py-2 text-xs font-semibold ${stateClass}`}
                                        >
                                            {state === "OK"
                                                ? "Present"
                                                : state === "STALE"
                                                    ? "Stale"
                                                    : "Missing"}
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </section>

            {/* Optional: last score run */}
            {lastScoreRun && (
                <section className="text-xs text-slate-500">
                    Last score run (from alerts.json):{" "}
                    <span className="font-mono">
                        {lastScoreRun.toISOString()}
                    </span>
                </section>
            )}
        </div>
    );
}