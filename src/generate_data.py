"""Generate a reproducible synthetic manufacturing-company audit dataset."""

from __future__ import annotations

import argparse
import csv
import random
from datetime import date, datetime, time, timedelta
from pathlib import Path


PRODUCTS = [
    ("Industrial sensor", 8_600, 0.66), ("Control module", 15_800, 0.70),
    ("Servo drive", 27_500, 0.72), ("Inspection camera", 42_000, 0.64),
    ("Robot arm", 186_000, 0.76), ("Production cell", 680_000, 0.79),
]
REGIONS = ["East China", "South China", "North China", "Central China", "West China", "Export"]
DEBITS = ["Accounts Receivable", "Cash", "Sales Returns", "Other Receivables", "Cost of Sales"]
CREDITS = ["Revenue", "Accounts Receivable", "Inventory", "Accrued Expenses", "Other Income"]


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def build_customers(rng: random.Random, count: int = 350) -> list[dict]:
    rows = []
    for i in range(1, count + 1):
        start = date(2017, 1, 1) + timedelta(days=rng.randrange(0, 3200))
        rows.append({
            "customer_id": f"C{i:04d}", "customer_name": f"Customer {i:04d}",
            "region": rng.choice(REGIONS), "onboarding_date": start.isoformat(),
            "credit_limit": rng.choice([500_000, 1_000_000, 2_000_000, 5_000_000, 10_000_000]),
        })
    return rows


def build_sales(rng: random.Random, customers: list[dict], count: int = 12_000) -> list[dict]:
    rows = []
    start = date(2025, 1, 1)
    for i in range(1, count + 1):
        customer = rng.choice(customers)
        invoice_date = start + timedelta(days=rng.randrange(0, 365))
        product, unit_price, cost_ratio = rng.choice(PRODUCTS)
        quantity = rng.randint(1, 12)
        amount = unit_price * quantity * rng.uniform(0.92, 1.08)
        shipment_date = invoice_date + timedelta(days=rng.choice([-1, 0, 0, 0, 1, 2]))
        recognition_date = shipment_date + timedelta(days=rng.choice([0, 0, 0, 1]))
        return_amount = amount * rng.uniform(0.4, 1) if rng.random() < 0.018 else 0

        # Seed known exceptions so demonstrations and tests are stable.
        if i % 997 == 0:
            invoice_date = date(2025, 12, 30)
            shipment_date = date(2026, 1, 4)
            recognition_date = invoice_date
            amount *= 5
        if i % 1301 == 0:
            amount = -abs(amount)
        if i % 887 == 0:
            cost_ratio = 0.25
        tenure = (invoice_date - date.fromisoformat(customer["onboarding_date"])).days
        rows.append({
            "transaction_id": f"INV{i:06d}", "customer_id": customer["customer_id"],
            "customer_name": customer["customer_name"], "region": customer["region"], "product": product,
            "invoice_date": invoice_date.isoformat(), "shipment_date": shipment_date.isoformat(),
            "recognition_date": recognition_date.isoformat(), "quantity": quantity,
            "sales_amount": round(amount, 2), "cost_amount": round(abs(amount) * cost_ratio, 2),
            "return_amount": round(abs(return_amount), 2), "customer_tenure_days": tenure,
        })
    return rows


def build_journals(rng: random.Random, count: int = 5_000) -> list[dict]:
    rows = []
    users = [("u001", "Accountant"), ("u002", "Accountant"), ("u003", "Senior Accountant"),
             ("u004", "Controller"), ("u005", "CFO"), ("batch", "System")]
    for i in range(1, count + 1):
        day = date(2025, 1, 1) + timedelta(days=rng.randrange(0, 365))
        hour = rng.choice(list(range(8, 19)))
        minute = rng.randrange(0, 60)
        debit, credit = rng.choice(DEBITS[:3]), rng.choice(CREDITS[:3])
        user, role = rng.choices(users, weights=[26, 25, 18, 4, 1, 35], k=1)[0]
        source = "automated" if user == "batch" else rng.choice(["manual", "manual", "subledger"])
        amount = round(10 ** rng.uniform(3, 6.2), 2)
        reversal = False
        if i % 389 == 0:
            day, hour, amount, user, role, source = date(2025, 12, 30), 23, 2_000_000, "u005", "CFO", "manual"
            debit, credit = "Other Receivables", "Other Income"
        if i % 613 == 0:
            reversal = True
        rows.append({
            "journal_id": f"JE{i:06d}", "posting_datetime": datetime.combine(day, time(hour, minute)).isoformat(),
            "debit_account": debit, "credit_account": credit, "amount": amount,
            "currency": "CNY", "source": source, "user_id": user, "user_role": role,
            "is_reversal": reversal, "description": "Synthetic journal entry for audit analytics",
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data")
    parser.add_argument("--sales", type=int, default=12000)
    parser.add_argument("--journals", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    rng = random.Random(args.seed)
    out = Path(args.output)
    customers = build_customers(rng)
    write_csv(out / "customers.csv", customers)
    write_csv(out / "sales.csv", build_sales(rng, customers, args.sales))
    write_csv(out / "journal_entries.csv", build_journals(rng, args.journals))
    print(f"Generated {args.sales:,} sales, {args.journals:,} journals and {len(customers):,} customers in {out}")


if __name__ == "__main__":
    main()
