import { z } from "zod";

export const HealthSchema = z.object({
    status: z.string(),
    artifact_dir: z.string(),
    artifacts_present: z.record(z.string(), z.boolean()),
    artifacts_mtime_utc: z.record(z.string(), z.string().nullable()),
});

export type Health = z.infer<typeof HealthSchema>;
