import { HealthSchema, type Health } from "./schemas/health";

const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function fetchHealth(): Promise<Health> {
    const res = await fetch(`${API_BASE_URL}/api/health`);
    if (!res.ok) {
        throw new Error(`Health request failed: ${res.status}`);
    }

    const json = await res.json();
    return HealthSchema.parse(json);
}