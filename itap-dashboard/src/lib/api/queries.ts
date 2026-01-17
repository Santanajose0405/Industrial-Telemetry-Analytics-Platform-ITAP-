import { fetchJson } from "./client";
import { HealthSchema, type Health } from "../schemas/health";

export const qk = {
    health: ["health"] as const,
};

export function getHealth(): Promise<Health> {
    return fetchJson("/api/health", HealthSchema);
}