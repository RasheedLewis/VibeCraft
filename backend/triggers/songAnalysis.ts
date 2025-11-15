import { task, wait } from "@trigger.dev/sdk";

const DEFAULT_API_BASE_URL = "http://localhost:8000/api/v1";

const getApiBaseUrl = () => {
  const envUrl = process.env.TRIGGER_BACKEND_API_BASE_URL?.trim();
  if (!envUrl) return DEFAULT_API_BASE_URL;
  return envUrl.replace(/\/+$/, "");
};

interface AnalyzeSongPayload {
  songId: string;
  pollIntervalMs?: number;
  timeoutMs?: number;
}

interface AnalyzeResponse {
  jobId: string;
  status: string;
}

interface JobStatusResponse {
  jobId: string;
  songId: string;
  status: "queued" | "processing" | "completed" | "failed";
  progress: number;
  analysisId?: string | null;
  error?: string | null;
  result?: unknown;
}

export const analyzeSongTask = task({
  id: "trigger-song-analysis",
  retry: {
    maxAttempts: 5,
    factor: 1.8,
    minTimeoutInMs: 1_000,
    maxTimeoutInMs: 30_000,
    randomize: true,
  },
  run: async (payload: AnalyzeSongPayload, { logger }) => {
    if (!payload?.songId) {
      throw new Error("songId is required to start analysis.");
    }

    const apiBaseUrl = getApiBaseUrl();
    const pollInterval = payload.pollIntervalMs ?? 5_000;
    const timeoutMs = payload.timeoutMs ?? 10 * 60 * 1_000; // 10 minutes

    logger.info("Enqueuing song analysis", {
      apiBaseUrl,
      songId: payload.songId,
    });

    const enqueueResponse = await fetch(`${apiBaseUrl}/songs/${payload.songId}/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!enqueueResponse.ok) {
      const detail = await safeParseJson(enqueueResponse);
      throw new Error(
        `Failed to enqueue song analysis (${enqueueResponse.status}): ${JSON.stringify(detail)}`
      );
    }

    const enqueueJson = (await enqueueResponse.json()) as AnalyzeResponse;
    const jobId = enqueueJson.jobId;

    logger.info("Job enqueued", { jobId, status: enqueueJson.status });

    const start = Date.now();

    while (true) {
      if (Date.now() - start > timeoutMs) {
        throw new Error(`Timed out waiting for analysis job ${jobId}`);
      }

      const statusResponse = await fetch(`${apiBaseUrl}/jobs/${jobId}`);
      if (!statusResponse.ok) {
        const detail = await safeParseJson(statusResponse);
        throw new Error(
          `Failed to fetch job status (${statusResponse.status}): ${JSON.stringify(detail)}`
        );
      }

      const statusJson = (await statusResponse.json()) as JobStatusResponse;
      logger.info("Job status", {
        jobId: statusJson.jobId,
        status: statusJson.status,
        progress: statusJson.progress,
      });

      if (statusJson.status === "completed") {
        return {
          jobId: statusJson.jobId,
          songId: statusJson.songId,
          analysisId: statusJson.analysisId,
          analysis: statusJson.result,
        };
      }

      if (statusJson.status === "failed") {
        throw new Error(
          `Song analysis failed for job ${jobId}: ${statusJson.error ?? "unknown error"}`
        );
      }

      await wait.for({ milliseconds: pollInterval });
    }
  },
});

async function safeParseJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return await response.text();
  }
}

