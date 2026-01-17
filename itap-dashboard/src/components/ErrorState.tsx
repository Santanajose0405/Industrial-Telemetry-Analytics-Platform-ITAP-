// src/components/ErrorState.tsx
type Props = {
    label?: string;
    error: unknown;
};

export default function ErrorState({ label, error }: Props) {
    return (
        <div className="p-6 text-red-600">
            {label ? `${label[0].toUpperCase()}${label.slice(1)} error` : "Error"}:{" "}
            {String(error)}
        </div>
    );
}
