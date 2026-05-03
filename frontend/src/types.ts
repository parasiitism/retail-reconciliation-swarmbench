export type DashboardStatus = "ready" | "empty";

export type Metrics = {
  net_revenue: string;
  gross_sales?: string;
  refunds?: string;
  validation_score: number;
  duplicates_found: number;
  unmapped_sku_count: number;
  source_count: number;
  transaction_count: number;
};

export type Job = {
  job_id: string;
  status: "pending" | "running" | "completed" | "failed";
  report_path: string | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
};

export type CategorySummary = {
  transaction_count: number;
  sale_count: number;
  refund_count: number;
  gross_sales: string;
  refunds: string;
  net_revenue: string;
};

export type SourceReport = {
  source_id: string;
  raw_row_count: number;
  transaction_count: number;
  sale_count: number;
  refund_count: number;
  gross_sales: string;
  refunds: string;
  net_revenue: string;
};

export type ReviewItem = {
  code: string;
  title: string;
  count: number;
  severity: "info" | "warning" | "error";
  message: string;
};

export type AuditEvent = {
  event_type: string;
  source_id: string;
  transaction_id: string | null;
  sku: string | null;
  message: string;
  severity: "info" | "warning" | "error";
};

export type DashboardSummary = {
  status: DashboardStatus;
  message?: string;
  latest_job?: Job;
  metrics: Metrics;
  recent_jobs: Job[];
  category_totals: Record<string, CategorySummary>;
  review_queue: ReviewItem[];
  audit_events: AuditEvent[];
};

export type ReconciliationReport = {
  source_count: number;
  raw_row_count: number;
  transaction_count: number;
  sale_count: number;
  refund_count: number;
  gross_sales: string;
  refunds: string;
  net_revenue: string;
  duplicate_transaction_ids: string[];
  unmapped_skus: string[];
  audit_events: AuditEvent[];
  category_totals: Record<string, CategorySummary>;
  source_reports: Record<string, SourceReport>;
};

export type JobReportResponse = {
  job: Job;
  report: ReconciliationReport;
};
