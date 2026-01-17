import { z } from "zod";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";
// If empty, Vite proxy will handle /api/*

export async function fetchJson<T>(
    path: string,
    schema: z.ZodType<T>,
    init?: RequestInit
): Promise<T> {
    const url = path.startsWith("http") ? path : `${API_BASE}${path}`;
    const res = await fetch(url, {
        ...init,
        headers: {
            "Content-Type": "application/json",
            ...(init?.headers ?? {}),
        },
    });

    if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(`HTTP ${res.status} ${res.statusText} ${text}`.trim());
    }

    const data = await res.json();
    return schema.parse(data);
}