// src/components/LoadingState.tsx
type Props = {
    label?: string;
};

export default function LoadingState({ label }: Props) {
    return (
        <div className="p-6 text-slate-500">
            {label ? `Loading ${label}…` : "Loading…"}
        </div>
    );
}
