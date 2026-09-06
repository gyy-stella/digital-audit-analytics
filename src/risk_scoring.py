"""Transparent, assertion-led audit risk scoring rules."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any


REVENUE_RULES = {
    "cutoff": 22,
    "post_period_return": 18,
    "high_value": 15,
    "negative_sale": 12,
    "margin_outlier": 11,
    "new_customer": 9,
    "date_mismatch": 13,
}

JOURNAL_RULES = {
    "period_end": 18,
    "weekend": 10,
    "late_night": 12,
    "round_amount": 10,
    "manual": 12,
    "management_user": 15,
    "rare_account_pair": 13,
    "reversal": 10,
}


def _as_date(value: str) -> date:
    return date.fromisoformat(value[:10])


def score_revenue(row: dict[str, Any], high_value_threshold: float = 1_000_000) -> dict[str, Any]:
    """Evaluate a sales transaction against audit-assertion risk rules."""
    invoice_date = _as_date(row["invoice_date"])
    shipment_date = _as_date(row["shipment_date"])
    recognition_date = _as_date(row["recognition_date"])
    amount = float(row["sales_amount"])
    cost = float(row["cost_amount"])
    return_amount = float(row.get("return_amount", 0) or 0)
    margin = (amount - cost) / abs(amount) if amount else 0

    flags = {
        "cutoff": invoice_date.month == 12 and invoice_date.day >= 28,
        "post_period_return": return_amount > 0 and return_amount / max(abs(amount), 1) >= 0.35,
        "high_value": abs(amount) >= high_value_threshold,
        "negative_sale": amount < 0,
        "margin_outlier": margin < 0.05 or margin > 0.60,
        "new_customer": row.get("customer_tenure_days", 9999) != "" and int(row["customer_tenure_days"]) < 90 and abs(amount) >= 300_000,
        "date_mismatch": recognition_date < shipment_date or abs((recognition_date - shipment_date).days) > 7,
    }
    score = min(100, sum(REVENUE_RULES[name] for name, hit in flags.items() if hit))
    reasons = [name.replace("_", " ") for name, hit in flags.items() if hit]
    return {"risk_score": score, "risk_level": risk_level(score), "risk_reasons": "; ".join(reasons), **flags}


def score_journal(row: dict[str, Any], pair_frequency: int = 99) -> dict[str, Any]:
    """Evaluate one journal entry; account-pair frequency is population-derived."""
    posted = datetime.fromisoformat(row["posting_datetime"])
    amount = abs(float(row["amount"]))
    flags = {
        "period_end": posted.month == 12 and posted.day >= 28,
        "weekend": posted.weekday() >= 5,
        "late_night": posted.hour < 6 or posted.hour >= 22,
        "round_amount": amount >= 100_000 and amount % 10_000 == 0,
        "manual": str(row.get("source", "")).lower() == "manual",
        "management_user": str(row.get("user_role", "")).lower() in {"controller", "cfo", "finance director"},
        "rare_account_pair": pair_frequency <= 2,
        "reversal": str(row.get("is_reversal", "")).lower() in {"true", "1", "yes"},
    }
    score = min(100, sum(JOURNAL_RULES[name] for name, hit in flags.items() if hit))
    reasons = [name.replace("_", " ") for name, hit in flags.items() if hit]
    return {"risk_score": score, "risk_level": risk_level(score), "risk_reasons": "; ".join(reasons), **flags}


def risk_level(score: int) -> str:
    if score >= 35:
        return "High"
    if score >= 15:
        return "Medium"
    return "Low"


def suggested_procedure(reasons: str, kind: str = "revenue") -> str:
    """Map explainable flags to a practical audit response."""
    reason_set = set(reasons.split("; ")) if reasons else set()
    if kind == "journal":
        if {"management user", "manual", "period end"}.issubset(reason_set):
            return "Inspect support, approval and business rationale; trace to consolidation entries"
        if "rare account pair" in reason_set:
            return "Inspect account mapping and corroborate the unusual debit/credit relationship"
        if "reversal" in reason_set:
            return "Agree to reversing entry and assess whether reversal masks period-end bias"
        return "Inspect journal support, preparer/approver and posting rationale"
    if "date mismatch" in reason_set or "cutoff" in reason_set:
        return "Inspect contract, invoice and proof of delivery; test cut-off"
    if "post period return" in reason_set:
        return "Inspect credit note and subsequent return; evaluate occurrence and variable consideration"
    if "new customer" in reason_set:
        return "Confirm balance and validate customer existence and commercial substance"
    if "margin outlier" in reason_set:
        return "Recalculate margin and inspect pricing approval and contract terms"
    return "Vouch transaction to contract, invoice, dispatch evidence and cash receipt"
