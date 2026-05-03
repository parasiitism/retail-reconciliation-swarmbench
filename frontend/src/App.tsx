import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  ClipboardCheck,
  Database,
  FileText,
  FileUp,
  Gauge,
  GitMerge,
  Layers3,
  ListChecks,
  Loader2,
  LucideIcon,
  RefreshCw,
  ShieldCheck,
  Upload,
  WalletCards,
} from "lucide-react";
import { ChangeEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";

import { fetchDashboardSummary, fetchJobReport, runDemoJob, uploadCsvFiles } from "./api";
import type {
  AuditEvent,
  CategorySummary,
  DashboardSummary,
  Job,
  ReconciliationReport,
  ReviewItem,
  SourceReport,
} from "./types";

type SectionId = "overview" | "jobs" | "reports" | "audit" | "storage";

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 2,
});

const compactNumberFormatter = new Intl.NumberFormat("en-US");

function formatMoney(value: string | undefined): string {
  return currencyFormatter.format(Number(value ?? 0));
}

function formatDateTime(value: string | null): string {
  if (!value) {
    return "Not completed";
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function App() {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const sectionRefs = useRef<Record<SectionId, HTMLElement | null>>({
    overview: null,
    jobs: null,
    reports: null,
    audit: null,
    storage: null,
  });
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [actionLabel, setActionLabel] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [selectedFileNames, setSelectedFileNames] = useState<string[]>([]);
  const [activeSection, setActiveSection] = useState<SectionId>("overview");
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [selectedReport, setSelectedReport] = useState<ReconciliationReport | null>(null);
  const [isJobDetailLoading, setIsJobDetailLoading] = useState(false);
  const [jobDetailError, setJobDetailError] = useState<string | null>(null);

  const loadSummary = useCallback(async () => {
    setErrorMessage(null);
    setIsLoading(true);

    try {
      const nextSummary = await fetchDashboardSummary();
      setSummary(nextSummary);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Unable to load dashboard");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadSummary();
  }, [loadSummary]);

  const handleRunDemo = async () => {
    setActionLabel("Running demo");
    setErrorMessage(null);
    setSuccessMessage(null);
    setSelectedFileNames([]);

    try {
      await runDemoJob();
      await loadSummary();
      setSuccessMessage("Demo reconciliation completed and dashboard metrics were refreshed.");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Demo job failed");
    } finally {
      setActionLabel(null);
    }
  };

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const { files } = event.target;

    if (!files || files.length === 0) {
      return;
    }

    setActionLabel("Uploading CSVs");
    setErrorMessage(null);
    setSuccessMessage(null);
    setSelectedFileNames(Array.from(files).map((file) => file.name));

    try {
      await uploadCsvFiles(files);
      await loadSummary();
      setSuccessMessage(`${files.length} CSV file${files.length === 1 ? "" : "s"} uploaded and reconciled.`);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "CSV upload failed");
    } finally {
      setActionLabel(null);
      event.target.value = "";
    }
  };

  const isBusy = isLoading || actionLabel !== null;
  const metrics = summary?.metrics;

  const handleNavigate = (sectionId: SectionId) => {
    setActiveSection(sectionId);
    sectionRefs.current[sectionId]?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };

  const handleSelectJob = async (job: Job) => {
    setSelectedJob(job);
    setSelectedReport(null);
    setJobDetailError(null);

    if (job.status !== "completed") {
      setJobDetailError("Reports are available after a job completes successfully.");
      return;
    }

    setIsJobDetailLoading(true);

    try {
      const response = await fetchJobReport(job.job_id);
      setSelectedJob(response.job);
      setSelectedReport(response.report);
    } catch (error) {
      setJobDetailError(error instanceof Error ? error.message : "Unable to load job report");
    } finally {
      setIsJobDetailLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <Sidebar activeSection={activeSection} onNavigate={handleNavigate} />

      <main className="dashboard">
        <header
          className="dashboard-header"
          ref={(element) => {
            sectionRefs.current.overview = element;
          }}
        >
          <div>
            <h1>Revenue Reconciliation Dashboard</h1>
            <p>Monitor reconciliation jobs, validation health, and review queues.</p>
          </div>

          <div className="header-actions">
            <button className="button secondary" onClick={loadSummary} disabled={isBusy}>
              <RefreshCw size={17} />
              Refresh
            </button>
            <button className="button secondary" onClick={handleRunDemo} disabled={isBusy}>
              {actionLabel === "Running demo" ? <Loader2 className="spin" size={17} /> : <Activity size={17} />}
              Run Demo
            </button>
            <button className="button primary" onClick={() => fileInputRef.current?.click()} disabled={isBusy}>
              {actionLabel === "Uploading CSVs" ? <Loader2 className="spin" size={17} /> : <Upload size={17} />}
              Upload CSVs
            </button>
            <input
              ref={fileInputRef}
              className="file-input"
              type="file"
              accept=".csv,text/csv"
              multiple
              onChange={handleFileChange}
            />
          </div>
        </header>

        {errorMessage && (
          <section className="notice error">
            <AlertTriangle size={18} />
            <span>{errorMessage}</span>
          </section>
        )}

        {successMessage && (
          <section className="notice success">
            <CheckCircle2 size={18} />
            <span>{successMessage}</span>
          </section>
        )}

        {selectedFileNames.length > 0 && (
          <section className="upload-feedback">
            <div className="upload-feedback-header">
              <FileUp size={18} />
              <div>
                <strong>Latest selected files</strong>
                <span>{selectedFileNames.length} file{selectedFileNames.length === 1 ? "" : "s"}</span>
              </div>
            </div>
            <div className="file-chip-list">
              {selectedFileNames.map((fileName) => (
                <span className="file-chip" key={fileName}>
                  {fileName}
                </span>
              ))}
            </div>
          </section>
        )}

        {isLoading && !summary ? (
          <section className="loading-panel">
            <Loader2 className="spin" size={24} />
            <span>Loading reconciliation dashboard</span>
          </section>
        ) : (
          <>
            <section className="metric-grid">
              <MetricCard
                icon={WalletCards}
                label="Net Revenue"
                value={formatMoney(metrics?.net_revenue)}
                accent="blue"
              />
              <MetricCard
                icon={ShieldCheck}
                label="Validation Score"
                value={`${metrics?.validation_score ?? 0}%`}
                accent="green"
              />
              <MetricCard
                icon={GitMerge}
                label="Duplicates Found"
                value={compactNumberFormatter.format(metrics?.duplicates_found ?? 0)}
                accent="violet"
              />
              <MetricCard
                icon={Layers3}
                label="Unmapped SKUs"
                value={compactNumberFormatter.format(metrics?.unmapped_sku_count ?? 0)}
                accent="amber"
              />
            </section>

            <Pipeline />

            <section className="dashboard-grid">
              <RecentJobs
                jobs={summary?.recent_jobs ?? []}
                selectedJobId={selectedJob?.job_id ?? null}
                onSelectJob={handleSelectJob}
                sectionRef={(element) => {
                  sectionRefs.current.jobs = element;
                }}
              />
              <JobDetailPanel
                errorMessage={jobDetailError}
                isLoading={isJobDetailLoading}
                job={selectedJob}
                report={selectedReport}
              />
              <ReviewQueue items={summary?.review_queue ?? []} />
              <CategoryRevenue
                categories={summary?.category_totals ?? {}}
                sectionRef={(element) => {
                  sectionRefs.current.reports = element;
                }}
              />
              <AuditTrail
                events={summary?.audit_events ?? []}
                sectionRef={(element) => {
                  sectionRefs.current.audit = element;
                }}
              />
              <StoragePanel
                sectionRef={(element) => {
                  sectionRefs.current.storage = element;
                }}
              />
            </section>
          </>
        )}
      </main>
    </div>
  );
}

type SidebarProps = {
  activeSection: SectionId;
  onNavigate: (sectionId: SectionId) => void;
};

function Sidebar({ activeSection, onNavigate }: SidebarProps) {
  const navItems = [
    { id: "overview", label: "Overview", icon: Gauge },
    { id: "jobs", label: "Jobs", icon: ListChecks },
    { id: "reports", label: "Reports", icon: FileText },
    { id: "audit", label: "Audit Trail", icon: ClipboardCheck },
    { id: "storage", label: "Storage", icon: Database },
  ];

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">R</div>
        <div>
          <strong>RevRecon</strong>
          <span>Multi-source reconciliation</span>
        </div>
      </div>

      <nav className="nav-list">
        {navItems.map((item) => (
          <button
            className={`nav-item ${activeSection === item.id ? "active" : ""}`}
            key={item.id}
            onClick={() => onNavigate(item.id as SectionId)}
            type="button"
          >
            <item.icon size={18} />
            {item.label}
          </button>
        ))}
      </nav>

      <div className="workspace-card">
        <Database size={18} />
        <div>
          <strong>SQLite Store</strong>
          <span>Local persistence</span>
        </div>
      </div>
    </aside>
  );
}

type MetricCardProps = {
  icon: LucideIcon;
  label: string;
  value: string;
  accent: "blue" | "green" | "violet" | "amber";
};

function MetricCard({ icon: Icon, label, value, accent }: MetricCardProps) {
  return (
    <article className="metric-card">
      <div className={`metric-icon ${accent}`}>
        <Icon size={24} />
      </div>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
    </article>
  );
}

function Pipeline() {
  const steps = [
    { label: "Connect", icon: FileUp },
    { label: "Map Schema", icon: GitMerge },
    { label: "Normalize", icon: Activity },
    { label: "Deduplicate", icon: Layers3 },
    { label: "Validate", icon: ShieldCheck },
    { label: "Report", icon: FileText },
  ];

  return (
    <section className="pipeline-panel">
      <div className="section-heading">
        <h2>Reconciliation Pipeline</h2>
        <span>Current backend flow</span>
      </div>

      <div className="pipeline-steps">
        {steps.map((step) => (
          <div className="pipeline-step" key={step.label}>
            <div className="step-node">
              <step.icon size={18} />
              <CheckCircle2 className="step-check" size={14} />
            </div>
            <strong>{step.label}</strong>
            <span>Ready</span>
          </div>
        ))}
      </div>
    </section>
  );
}

type SectionRef = (element: HTMLElement | null) => void;

function RecentJobs({
  jobs,
  onSelectJob,
  sectionRef,
  selectedJobId,
}: {
  jobs: Job[];
  onSelectJob: (job: Job) => void;
  sectionRef: SectionRef;
  selectedJobId: string | null;
}) {
  return (
    <section className="panel wide scroll-target" ref={sectionRef}>
      <div className="section-heading">
        <h2>Recent Jobs</h2>
        <span>{jobs.length} persisted</span>
      </div>

      <div className="table">
        <div className="table-row table-head">
          <span>Job ID</span>
          <span>Status</span>
          <span>Created</span>
          <span>Completed</span>
        </div>

        {jobs.length === 0 ? (
          <EmptyRow message="No jobs yet. Run a demo or upload CSVs." />
        ) : (
          jobs.map((job) => (
            <button
              className={`table-row job-row ${selectedJobId === job.job_id ? "selected" : ""}`}
              key={job.job_id}
              onClick={() => onSelectJob(job)}
              type="button"
            >
              <span className="mono">{job.job_id.slice(0, 8)}</span>
              <StatusPill status={job.status} />
              <span>{formatDateTime(job.created_at)}</span>
              <span>{formatDateTime(job.completed_at)}</span>
            </button>
          ))
        )}
      </div>
    </section>
  );
}

function JobDetailPanel({
  errorMessage,
  isLoading,
  job,
  report,
}: {
  errorMessage: string | null;
  isLoading: boolean;
  job: Job | null;
  report: ReconciliationReport | null;
}) {
  return (
    <section className="panel job-detail-panel">
      <div className="section-heading report-detail-heading">
        <h2>Report Details</h2>
        {job ? (
          <div className="detail-actions">
            <span>{job.job_id.slice(0, 8)}</span>
            {report && (
              <a
                className="mini-link"
                href={`/api/jobs/${job.job_id}/report`}
                rel="noreferrer"
                target="_blank"
              >
                <FileText size={14} />
                Open JSON
              </a>
            )}
          </div>
        ) : (
          <span>Select a job</span>
        )}
      </div>

      {!job && (
        <div className="detail-empty">
          <FileText size={20} />
          <p>Click a completed job row to inspect source reports, category totals, and review signals.</p>
        </div>
      )}

      {job && (
        <div className="job-detail-body">
          <div className="job-detail-meta">
            <span className="mono">{job.job_id}</span>
            <StatusPill status={job.status} />
          </div>

          {isLoading && (
            <div className="detail-loading">
              <Loader2 className="spin" size={18} />
              Loading report
            </div>
          )}

          {errorMessage && !isLoading && (
            <div className="detail-error">
              <AlertTriangle size={17} />
              <span>{errorMessage}</span>
            </div>
          )}

          {report && !isLoading && (
            <>
              <div className="detail-metrics">
                <DetailStat label="Net Revenue" value={formatMoney(report.net_revenue)} />
                <DetailStat label="Gross Sales" value={formatMoney(report.gross_sales)} />
                <DetailStat label="Refunds" value={formatMoney(report.refunds)} />
                <DetailStat label="Transactions" value={compactNumberFormatter.format(report.transaction_count)} />
                <DetailStat label="Raw Rows" value={compactNumberFormatter.format(report.raw_row_count)} />
                <DetailStat label="Sources" value={compactNumberFormatter.format(report.source_count)} />
                <DetailStat
                  label="Duplicates"
                  value={compactNumberFormatter.format(report.duplicate_transaction_ids.length)}
                />
                <DetailStat label="Unmapped SKUs" value={compactNumberFormatter.format(report.unmapped_skus.length)} />
              </div>

              <SourceReportTable reports={report.source_reports} />
              <ReportCategoryBreakdown categories={report.category_totals} />
              <div className="report-review-grid">
                <TokenList
                  emptyLabel="No duplicate transactions in this report."
                  label="Duplicate IDs"
                  tokens={report.duplicate_transaction_ids}
                />
                <TokenList
                  emptyLabel="No unmapped SKUs in this report."
                  label="Unmapped SKUs"
                  tokens={report.unmapped_skus}
                />
              </div>
              <ReportAuditEvents events={report.audit_events} />
            </>
          )}
        </div>
      )}
    </section>
  );
}

function ReportAuditEvents({ events }: { events: AuditEvent[] }) {
  return (
    <div className="report-section">
      <div className="report-section-heading">
        <strong>Selected Job Audit Trail</strong>
        <span>{events.length} event{events.length === 1 ? "" : "s"}</span>
      </div>

      {events.length === 0 ? (
        <p className="empty-copy">No audit events were produced for this job.</p>
      ) : (
        <div className="report-audit-list">
          {events.map((event, index) => (
            <article className="report-audit-item" key={`${event.event_type}-${event.source_id}-${index}`}>
              <div className={`audit-icon ${event.severity}`}>
                <AlertTriangle size={16} />
              </div>
              <div>
                <div className="report-audit-title">
                  <strong>{event.event_type.replaceAll("_", " ")}</strong>
                  <span>{event.source_id}</span>
                </div>
                <p>{event.message}</p>
                <div className="audit-token-row">
                  {event.transaction_id && <span>{event.transaction_id}</span>}
                  {event.sku && <span>{event.sku}</span>}
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}

function SourceReportTable({ reports }: { reports: Record<string, SourceReport> }) {
  const rows = useMemo(
    () =>
      Object.values(reports).sort(
        (first, second) => Number(second.net_revenue) - Number(first.net_revenue),
      ),
    [reports],
  );

  return (
    <div className="report-section">
      <div className="report-section-heading">
        <strong>Source Reports</strong>
        <span>{rows.length} source{rows.length === 1 ? "" : "s"}</span>
      </div>

      {rows.length === 0 ? (
        <p className="empty-copy">No source-level reports are available for this job.</p>
      ) : (
        <div className="source-report-table">
          <div className="source-report-row source-report-head">
            <span>Source</span>
            <span>Rows</span>
            <span>Txns</span>
            <span>Sales</span>
            <span>Refunds</span>
            <span>Net</span>
          </div>

          {rows.map((source) => (
            <div className="source-report-row" key={source.source_id}>
              <strong>{source.source_id.replaceAll("_", " ")}</strong>
              <span>{compactNumberFormatter.format(source.raw_row_count)}</span>
              <span>{compactNumberFormatter.format(source.transaction_count)}</span>
              <span>{formatMoney(source.gross_sales)}</span>
              <span>{formatMoney(source.refunds)}</span>
              <span>{formatMoney(source.net_revenue)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ReportCategoryBreakdown({ categories }: { categories: Record<string, CategorySummary> }) {
  const rows = useMemo(() => {
    const entries = Object.entries(categories);
    const maxRevenue = Math.max(...entries.map(([, value]) => Number(value.net_revenue)), 1);

    return entries
      .map(([category, value]) => ({
        category,
        value,
        width: Math.max(6, (Number(value.net_revenue) / maxRevenue) * 100),
      }))
      .sort((first, second) => Number(second.value.net_revenue) - Number(first.value.net_revenue));
  }, [categories]);

  return (
    <div className="report-section">
      <div className="report-section-heading">
        <strong>Category Breakdown</strong>
        <span>{rows.length} categories</span>
      </div>

      {rows.length === 0 ? (
        <p className="empty-copy">No category totals are available for this job.</p>
      ) : (
        <div className="report-category-list">
          {rows.map((row) => (
            <div className="report-category-row" key={row.category}>
              <div className="report-category-topline">
                <strong>{row.category.replaceAll("_", " ")}</strong>
                <span>{formatMoney(row.value.net_revenue)}</span>
              </div>
              <div className="bar-track">
                <div className="bar-fill" style={{ width: `${row.width}%` }} />
              </div>
              <div className="report-category-meta">
                <span>{compactNumberFormatter.format(row.value.transaction_count)} transactions</span>
                <span>{formatMoney(row.value.gross_sales)} sales</span>
                <span>{formatMoney(row.value.refunds)} refunds</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function DetailStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="detail-stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function TokenList({
  emptyLabel,
  label,
  tokens,
}: {
  emptyLabel: string;
  label: string;
  tokens: string[];
}) {
  return (
    <div className="token-section">
      <span>{label}</span>
      {tokens.length === 0 ? (
        <p>{emptyLabel}</p>
      ) : (
        <div className="file-chip-list">
          {tokens.map((token) => (
            <span className="file-chip" key={token}>
              {token}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function CategoryRevenue({
  categories,
  sectionRef,
}: {
  categories: Record<string, CategorySummary>;
  sectionRef: SectionRef;
}) {
  const rows = useMemo(() => {
    const entries = Object.entries(categories);
    const maxRevenue = Math.max(...entries.map(([, value]) => Number(value.net_revenue)), 1);

    return entries
      .map(([category, value]) => ({
        category,
        value,
        width: Math.max(6, (Number(value.net_revenue) / maxRevenue) * 100),
      }))
      .sort((a, b) => Number(b.value.net_revenue) - Number(a.value.net_revenue));
  }, [categories]);

  return (
    <section className="panel scroll-target" ref={sectionRef}>
      <div className="section-heading">
        <h2>Category Revenue</h2>
        <span>{rows.length} categories</span>
      </div>

      <div className="category-list">
        {rows.length === 0 ? (
          <p className="empty-copy">No category totals available yet.</p>
        ) : (
          rows.map((row) => (
            <div className="category-row" key={row.category}>
              <div className="category-label">
                <span>{row.category.replaceAll("_", " ")}</span>
                <strong>{formatMoney(row.value.net_revenue)}</strong>
              </div>
              <div className="bar-track">
                <div className="bar-fill" style={{ width: `${row.width}%` }} />
              </div>
            </div>
          ))
        )}
      </div>
    </section>
  );
}

function ReviewQueue({ items }: { items: ReviewItem[] }) {
  return (
    <section className="panel">
      <div className="section-heading">
        <h2>Review Queue</h2>
        <span>{items.length} active</span>
      </div>

      <div className="review-list">
        {items.length === 0 ? (
          <p className="empty-copy">No review items. Latest report passed validation.</p>
        ) : (
          items.map((item) => (
            <article className={`review-item ${item.severity}`} key={item.code}>
              <strong>{item.count}</strong>
              <div>
                <span>{item.title}</span>
                <p>{item.message}</p>
              </div>
            </article>
          ))
        )}
      </div>
    </section>
  );
}

function AuditTrail({ events, sectionRef }: { events: AuditEvent[]; sectionRef: SectionRef }) {
  return (
    <section className="panel scroll-target" ref={sectionRef}>
      <div className="section-heading">
        <h2>Audit Trail</h2>
        <span>{events.length} events</span>
      </div>

      <div className="audit-list">
        {events.length === 0 ? (
          <p className="empty-copy">No audit events available yet.</p>
        ) : (
          events.map((event, index) => (
            <article className="audit-item" key={`${event.event_type}-${event.source_id}-${index}`}>
              <div className={`audit-icon ${event.severity}`}>
                <AlertTriangle size={16} />
              </div>
              <div>
                <strong>{event.event_type.replaceAll("_", " ")}</strong>
                <p>{event.message}</p>
              </div>
            </article>
          ))
        )}
      </div>
    </section>
  );
}

function StoragePanel({ sectionRef }: { sectionRef: SectionRef }) {
  return (
    <section className="panel scroll-target">
      <div
        ref={sectionRef}
        className="section-heading"
      >
        <h2>Storage</h2>
        <span>Local mode</span>
      </div>

      <div className="storage-list">
        <article className="storage-item">
          <Database size={19} />
          <div>
            <strong>SQLite job store</strong>
            <p>Job metadata persists in <span>data/reconciliation.db</span>.</p>
          </div>
        </article>
        <article className="storage-item">
          <FileText size={19} />
          <div>
            <strong>JSON report artifacts</strong>
            <p>Completed reports are written under <span>outputs/reports</span>.</p>
          </div>
        </article>
        <article className="storage-item">
          <Upload size={19} />
          <div>
            <strong>Uploaded source files</strong>
            <p>CSV uploads are grouped by job under <span>uploads</span>.</p>
          </div>
        </article>
      </div>
    </section>
  );
}

function StatusPill({ status }: { status: Job["status"] }) {
  return <span className={`status-pill ${status}`}>{status}</span>;
}

function EmptyRow({ message }: { message: string }) {
  return (
    <div className="table-row empty-row">
      <span>{message}</span>
    </div>
  );
}

export default App;
