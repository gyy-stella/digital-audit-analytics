# AuditLens — Digital Audit Analytics Platform

An independent, full-population audit analytics project for **revenue recognition** and **journal entry testing**. It turns synthetic ERP-style data into explainable risk flags, risk-based audit samples, and procedure-specific audit responses.

> This is a portfolio demonstration using synthetic data. It is not affiliated with any audit firm and does not constitute an audit opinion.

## What the platform does

```text
Synthetic ERP populations
        ↓
Data integrity & full-population tests
        ↓
Assertion-led exception rules
        ↓
Explainable 0–100 risk scores
        ↓
70% targeted + 30% random sampling
        ↓
Suggested audit procedures and exportable findings
```

### Revenue Audit Analytics

- Year-end cut-off concentration
- Post-period returns over 35% of the original sale
- Population-derived high-value threshold (98th percentile)
- Negative / credit sales
- Gross-margin outliers
- High-value transactions with new customers
- Shipment-to-recognition date mismatch
- Risk-based sample recommendation mapped to occurrence, cut-off and accuracy

### Journal Entry Testing

- Period-end, weekend and late-night postings
- Large round-number entries
- Manual entries and management-level users
- Rare debit / credit account combinations
- Reversing entries
- Benford first-digit screening
- Targeted procedures for management override risk

## Quick start

Python 3.10+ is the only requirement; the pipeline deliberately uses the standard library so it runs anywhere.

```bash
python src/generate_data.py
python src/analytics.py
python -m http.server 8000 -d dashboard
```

Open `http://localhost:8000`. To run the tests:

```bash
python -m unittest discover -s tests -v
```

## Repository map

```text
dashboard/                 Interactive zero-dependency web dashboard
data/                      Reproducible synthetic source populations
outputs/                   Scored populations, samples and summary JSON
src/generate_data.py       Seeded ERP-style data generator
src/risk_scoring.py        Transparent audit rule definitions
src/audit_sampling.py      Targeted + random sample selection
src/analytics.py           End-to-end analytics pipeline
sql/                       Revenue and journal-entry audit queries
tests/                     Unit tests for rules and sampling
```

## Risk methodology

Every result is traceable to an explicit rule. Scores prioritize review; they do not label fraud.

| Revenue signal | Weight | Relevant assertion |
|---|---:|---|
| Year-end cut-off | 22 | Cut-off |
| Material post-period return | 18 | Occurrence / accuracy |
| High-value transaction | 15 | Occurrence |
| Negative sale | 12 | Accuracy / classification |
| Margin outlier | 11 | Accuracy |
| New customer + high value | 9 | Occurrence |
| Shipment / recognition mismatch | 13 | Cut-off |

Journal entries use a separate rule set covering timing, source, preparer authority, round amounts, rare account pairs and reversals. `High ≥ 35`, `Medium ≥ 15`, otherwise `Low`.

## Important design choices

- **Audit-first, not model-first:** tests originate from assertions and management-override risks.
- **Explainability:** every score exposes its contributing reasons and a suggested procedure.
- **Population context:** the high-value threshold and rare account pairs derive from the complete population.
- **Reproducibility:** deterministic generation and seeded sampling make results stable and reviewable.
- **No false assurance:** Benford analysis and risk scores are screening tools, never standalone fraud conclusions.

## 中文简介

AuditLens 是一个小型数字化审计分析平台，以制造业合成数据模拟完整收入交易总体和总账分录总体。项目覆盖收入截止性、期后退货、毛利异常、新客户大额交易、收入确认日期异常，以及期末/深夜/手工/管理层/整数金额/稀有科目组合等分录风险。系统将异常规则、可解释风险评分、风险导向抽样和建议审计程序串成完整审计链路，适合作为数字化审计岗位作品集。

## Disclaimer

The sample entity, users, customers, transactions and journals are fictional. Rules and weights are illustrative and must be calibrated to the entity, reporting framework, materiality, controls and engagement risk assessment before professional use.
