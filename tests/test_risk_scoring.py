import unittest

from src.audit_sampling import select_samples
from src.risk_scoring import risk_level, score_journal, score_revenue


class RiskScoringTests(unittest.TestCase):
    def test_revenue_cutoff_and_date_mismatch(self):
        row = {"invoice_date": "2025-12-30", "shipment_date": "2026-01-04",
               "recognition_date": "2025-12-30", "sales_amount": "2000000",
               "cost_amount": "1400000", "return_amount": "0", "customer_tenure_days": "500"}
        result = score_revenue(row)
        self.assertTrue(result["cutoff"])
        self.assertTrue(result["date_mismatch"])
        self.assertTrue(result["high_value"])
        self.assertEqual(result["risk_level"], "High")

    def test_high_risk_journal(self):
        row = {"posting_datetime": "2025-12-30T23:10:00", "amount": "2000000",
               "source": "manual", "user_role": "CFO", "is_reversal": "false"}
        result = score_journal(row, pair_frequency=1)
        self.assertGreaterEqual(result["risk_score"], 50)
        self.assertIn("management user", result["risk_reasons"])

    def test_sampling_is_deterministic(self):
        rows = [{"risk_score": i, "amount": i * 100} for i in range(20)]
        first = select_samples([dict(x) for x in rows], 10, seed=7)
        second = select_samples([dict(x) for x in rows], 10, seed=7)
        self.assertEqual([x["amount"] for x in first], [x["amount"] for x in second])

    def test_risk_bands(self):
        self.assertEqual(risk_level(14), "Low")
        self.assertEqual(risk_level(15), "Medium")
        self.assertEqual(risk_level(35), "High")


if __name__ == "__main__":
    unittest.main()
