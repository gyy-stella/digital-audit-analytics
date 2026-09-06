"""Run the full-population revenue and journal-entry analytics pipeline."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from statistics import median

try:
    from .audit_sampling import select_samples
    from .risk_scoring import score_journal, score_revenue, suggested_procedure
except ImportError:
    from audit_sampling import select_samples
    from risk_scoring import score_journal, score_revenue, suggested_procedure


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        fieldnames = list(dict.fromkeys(key for row in rows for key in row))
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def monthly_sales(rows: list[dict]) -> list[dict]:
    grouped: dict[str, float] = defaultdict(float)
    flagged: dict[str, float] = defaultdict(float)
    for row in rows:
        month = row["invoice_date"][:7]
        grouped[month] += float(row["sales_amount"])
        if row["risk_level"] == "High":
            flagged[month] += float(row["sales_amount"])
    return [{"month": month, "revenue": round(grouped[month], 2), "high_risk_revenue": round(flagged[month], 2)} for month in sorted(grouped)]


def benford(rows: list[dict]) -> list[dict]:
    import math
    observed = Counter()
    for row in rows:
        digits = str(int(abs(float(row["amount"]))))
        if digits and digits[0] != "0":
            observed[int(digits[0])] += 1
    total = sum(observed.values()) or 1
    return [{"digit": d, "observed": round(observed[d] / total, 4), "expected": round(math.log10(1 + 1 / d), 4)} for d in range(1, 10)]


def reason_counts(rows: list[dict]) -> list[dict]:
    counts = Counter()
    for row in rows:
        for reason in row.get("risk_reasons", "").split("; "):
            if reason:
                counts[reason] += 1
    return [{"reason": name, "count": count} for name, count in counts.most_common()]


def analyze(data_dir: Path, output_dir: Path) -> dict:
    sales = read_csv(data_dir / "sales.csv")
    journals = read_csv(data_dir / "journal_entries.csv")

    positive_amounts = sorted(abs(float(row["sales_amount"])) for row in sales if float(row["sales_amount"]) > 0)
    high_value_threshold = positive_amounts[max(0, int(len(positive_amounts) * 0.98) - 1)]
    scored_sales = []
    for row in sales:
        result = score_revenue(row, high_value_threshold)
        scored_sales.append({**row, **result, "amount": row["sales_amount"],
                             "suggested_procedure": suggested_procedure(result["risk_reasons"])})

    pair_counts = Counter((row["debit_account"], row["credit_account"]) for row in journals)
    scored_journals = []
    for row in journals:
        result = score_journal(row, pair_counts[(row["debit_account"], row["credit_account"])])
        scored_journals.append({**row, **result,
                                "suggested_procedure": suggested_procedure(result["risk_reasons"], "journal")})

    samples = select_samples(scored_sales, 60) + select_samples(scored_journals, 40, seed=43)
    high_sales = [row for row in scored_sales if row["risk_level"] == "High"]
    high_journals = [row for row in scored_journals if row["risk_level"] == "High"]
    total_revenue = sum(float(row["sales_amount"]) for row in scored_sales)
    flagged_revenue = sum(float(row["sales_amount"]) for row in high_sales)

    summary = {
        "meta": {"entity": "Aurora Industrial Automation Co. (synthetic)", "period": "FY2025",
                 "generated_on": date.today().isoformat(), "currency": "CNY",
                 "disclaimer": "Synthetic demonstration data. Not an audit opinion."},
        "kpis": {"transactions_analyzed": len(scored_sales), "journal_entries_analyzed": len(scored_journals),
                 "total_revenue": round(total_revenue, 2), "high_risk_transactions": len(high_sales),
                 "high_risk_revenue": round(flagged_revenue, 2), "unusual_journal_entries": len(high_journals),
                 "recommended_samples": len(samples), "high_value_threshold": round(high_value_threshold, 2)},
        "monthly_revenue": monthly_sales(scored_sales),
        "revenue_reasons": reason_counts(scored_sales), "journal_reasons": reason_counts(scored_journals),
        "top_revenue": sorted(scored_sales, key=lambda x: (x["risk_score"], abs(float(x["amount"]))), reverse=True)[:20],
        "top_journals": sorted(scored_journals, key=lambda x: (x["risk_score"], abs(float(x["amount"]))), reverse=True)[:20],
        "benford": benford(scored_journals),
        "risk_distribution": {
            "revenue": dict(Counter(row["risk_level"] for row in scored_sales)),
            "journals": dict(Counter(row["risk_level"] for row in scored_journals)),
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "revenue_scored.csv", scored_sales)
    write_csv(output_dir / "journals_scored.csv", scored_journals)
    write_csv(output_dir / "audit_samples.csv", samples)
    (output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (Path("dashboard") / "analytics-data.js").write_text(
        "window.AUDIT_DATA = " + json.dumps(summary, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data")
    parser.add_argument("--output", default="outputs")
    args = parser.parse_args()
    summary = analyze(Path(args.data), Path(args.output))
    print(json.dumps(summary["kpis"], indent=2))


if __name__ == "__main__":
    main()
