// src/lib/schemas/alerts.ts
import { z } from "zod";

export const AlertSchema = z.object({
    timestamp_utc: z.string(),         // e.g. "2026-01-15T02:15:05Z"
    device_id: z.string(),             // e.g. "PUMP-001"
    severity: z.union([
        z.enum(["INFO", "WARNING", "CRITICAL"]),
        z.string(),                      // fallback for any custom severity labels
    ]),
    route: z.string(),                 // e.g. "maintenance", "thermal"
    message: z.string(),               // human-readable text
});

export const AlertsSchema = z.array(AlertSchema);

export type Alert = z.infer<typeof AlertSchema>;
export type Alerts = z.infer<typeof AlertsSchema>;
