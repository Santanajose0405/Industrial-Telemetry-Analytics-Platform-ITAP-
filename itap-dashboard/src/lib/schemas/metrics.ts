// src/lib/schemas/metrics.ts
import { z } from "zod";

export const MetricPointSchema = z.object({
    ts_utc: z.string(),        // timestamp
    anomaly_rate: z.number(),  // 0–1, or percent
});

export const MetricsSchema = z.array(MetricPointSchema);

export type MetricPoint = z.infer<typeof MetricPointSchema>;
export type Metrics = z.infer<typeof MetricsSchema>;
