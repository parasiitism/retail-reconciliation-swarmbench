from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class CanonicalTransaction(BaseModel):
    transaction_id: str
    source_id: str
    transaction_date: str
    sku: str
    category: str = "unknown"
    quantity: int
    unit_price: Decimal
    transaction_type: Literal["sale", "refund"]
    amount: Decimal


class ReconciliationReport(BaseModel):
    source_id: str
    raw_row_count: int
    transaction_count: int
    sale_count: int
    refund_count: int
    gross_sales: Decimal
    refunds: Decimal
    net_revenue: Decimal


class CategorySummary(BaseModel):
    transaction_count: int
    sale_count: int
    refund_count: int
    gross_sales: Decimal
    refunds: Decimal
    net_revenue: Decimal


class AuditEvent(BaseModel):
    event_type: Literal["duplicate_skipped", "unmapped_sku"]
    source_id: str
    transaction_id: str | None = None
    sku: str | None = None
    message: str
    severity: Literal["info", "warning", "error"]


class MultiSourceReconciliationReport(BaseModel):
    source_count: int
    raw_row_count: int
    transaction_count: int
    sale_count: int
    refund_count: int
    gross_sales: Decimal
    refunds: Decimal
    net_revenue: Decimal
    audit_events: list[AuditEvent]
    duplicate_transaction_ids: list[str]
    unmapped_skus: list[str]
    category_totals: dict[str, CategorySummary]
    source_reports: dict[str, ReconciliationReport]

class ValidationIssue(BaseModel):
    code: str
    message: str
    severity: Literal["info", "warning", "error"]


class ValidationResult(BaseModel):
    is_valid: bool
    issue_count: int
    issues: list[ValidationIssue]

class ReconciliationJob(BaseModel):
    job_id:str
    status:Literal["pending","running","completed","failed"]
    report_path:str | None=None 
    error_message:str | None=None
    created_at:str 
    completed_at:str | None=None