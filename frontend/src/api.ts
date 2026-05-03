import type { DashboardSummary, JobReportResponse } from "./types";

async function parseJsonResponse<T>(response: Response): Promise<T> {
  const payload = await response.json();

  if (!response.ok) {
    const detail = payload?.detail ?? "Request failed";
    throw new Error(detail);
  }

  return payload as T;
}

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  const response = await fetch("/api/dashboard/summary");
  return parseJsonResponse<DashboardSummary>(response);
}

export async function fetchJobReport(jobId: string): Promise<JobReportResponse> {
  const response = await fetch(`/api/jobs/${jobId}/report`);
  return parseJsonResponse<JobReportResponse>(response);
}

export async function runDemoJob(): Promise<void> {
  const response = await fetch("/api/jobs/demo", {
    method: "POST",
  });

  await parseJsonResponse(response);
}

export async function uploadCsvFiles(files: FileList): Promise<void> {
  const formData = new FormData();

  Array.from(files).forEach((file) => {
    formData.append("files", file);
  });

  const response = await fetch("/api/jobs/upload-csv", {
    method: "POST",
    body: formData,
  });

  await parseJsonResponse(response);
}
