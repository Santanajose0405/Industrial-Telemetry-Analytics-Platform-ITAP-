// src/lib/schemas/aggregates.ts
import { z } from "zod";

export const AggregateBucketSchema = z.object({
    bucket: z.string(),        // e.g. "last_1h", "last_24h"
    devices: z.number(),
    alerts: z.number(),
    avg_severity: z.number(),  // numeric severity index, e.g. 1–3
});

export const AggregatesSchema = z.array(AggregateBucketSchema);

export type AggregateBucket = z.infer<typeof AggregateBucketSchema>;
export type Aggregates = z.infer<typeof AggregatesSchema>;
