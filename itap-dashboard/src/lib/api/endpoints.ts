// src/api/endpoints.ts
export const API_ENDPOINTS = {
    health: "/api/health",
    alerts: "/api/alerts",
    aggregates: "/api/aggregates",
    metrics: "/api/metrics",
} as const;

export type ApiEndpointKey = keyof typeof API_ENDPOINTS;
