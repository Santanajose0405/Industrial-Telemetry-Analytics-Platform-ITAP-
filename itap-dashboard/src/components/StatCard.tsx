// src/components/StatCard.tsx
type Tone = "default" | "success" | "warning" | "danger";

type Props = {
    title: string;
    value: React.ReactNode;
    subtitle?: React.ReactNode;
    tone?: Tone;
};

const toneClasses: Record<Tone, string> = {
    default: "text-slate-900",
    success: "text-emerald-600",
    warning: "text-amber-600",
    danger: "text-rose-600",
};

export default function StatCard({ title, value, subtitle, tone = "default" }: Props) {
    return (
        <div className="rounded-xl border bg-white p-5 shadow-sm">
            <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                {title}
            </div>
            <div className={`mt-3 text-xl font-semibold ${toneClasses[tone]}`}>{value}</div>
            {subtitle && (
                <p className="mt-2 text-xs text-slate-500">
                    {subtitle}
                </p>
            )}
        </div>
    );
}
