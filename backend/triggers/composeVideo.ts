import { task, wait } from "@trigger.dev/sdk";

const DEFAULT_API_BASE_URL = "http://localhost:8000/api/v1";

const getApiBaseUrl = () => {
  const envUrl = process.env.TRIGGER_BACKEND_API_BASE_URL?.trim();
  if (!envUrl) return DEFAULT_API_BASE_URL;
  return envUrl.replace(/\/+$/, "");
};

interface ComposeVideoPayload {
  jobId: string;
  songId: string;
  pollIntervalMs?: number;
  timeoutMs?: number;
}

interface CompositionJobStatusResponse {
  jobId: string;
  songId: string;
  status: "queued" | "processing" | "completed" | "failed" | "cancelled";
  progress: number;
  composedVideoId?: string | null;
  error?: string | null;
  createdAt: string;
  updatedAt: string;
}

export const composeVideoTask = task({
  id: "trigger-compose-video",
  retry: {
    maxAttempts: 3,
    factor: 1.8,
    minTimeoutInMs: 1_000,
    maxTimeoutInMs: 30_000,
    randomize: true,
  },
  run: async (payload: ComposeVideoPayload, { logger }) => {
    if (!payload?.jobId || !payload?.songId) {
      throw new Error("jobId and songId are required to compose video.");
    }

    const apiBaseUrl = getApiBaseUrl();
    const pollInterval = payload.pollIntervalMs ?? 10_000; // 10 seconds default (composition takes longer)
    const timeoutMs = payload.timeoutMs ?? 30 * 60 * 1_000; // 30 minutes default

    logger.info("Starting video composition", {
      apiBaseUrl,
      jobId: payload.jobId,
      songId: payload.songId,
    });

    // Trigger the composition execution on the backend
    const executeResponse = await fetch(
      `${apiBaseUrl}/songs/${payload.songId}/compose/${payload.jobId}/execute`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    if (!executeResponse.ok) {
      const detail = await safeParseJson(executeResponse);
      throw new Error(
        `Failed to execute composition (${executeResponse.status}): ${JSON.stringify(detail)}`
      );
    }

    logger.info("Composition execution started", { jobId: payload.jobId });

    const start = Date.now();

    // Poll for job completion
    while (true) {
      if (Date.now() - start > timeoutMs) {
        throw new Error(`Timed out waiting for composition job ${payload.jobId}`);
      }

      const statusResponse = await fetch(
        `${apiBaseUrl}/songs/${payload.songId}/compose/${payload.jobId}/status`
      );
      if (!statusResponse.ok) {
        const detail = await safeParseJson(statusResponse);
        throw new Error(
          `Failed to fetch job status (${statusResponse.status}): ${JSON.stringify(detail)}`
        );
      }

      const statusJson = (await statusResponse.json()) as CompositionJobStatusResponse;
      logger.info("Job status", {
        jobId: statusJson.jobId,
        status: statusJson.status,
        progress: statusJson.progress,
      });

      if (statusJson.status === "completed") {
        return {
          jobId: statusJson.jobId,
          songId: statusJson.songId,
          composedVideoId: statusJson.composedVideoId,
        };
      }

      if (statusJson.status === "failed") {
        throw new Error(
          `Video composition failed for job ${payload.jobId}: ${statusJson.error ?? "unknown error"}`
        );
      }

      if (statusJson.status === "cancelled") {
        throw new Error(`Video composition was cancelled for job ${payload.jobId}`);
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

