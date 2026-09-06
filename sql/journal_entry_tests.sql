-- Journal entry testing examples.

-- 1. Period-end manual journals posted by management
SELECT *
FROM journal_entries
WHERE posting_datetime >= '2025-12-28'
  AND LOWER(source) = 'manual'
  AND LOWER(user_role) IN ('controller', 'cfo', 'finance director')
ORDER BY ABS(amount) DESC;

-- 2. Large round-number journals
SELECT *
FROM journal_entries
WHERE ABS(amount) >= 100000 AND CAST(ABS(amount) AS INTEGER) % 10000 = 0;

-- 3. Rare account combinations
WITH pair_frequency AS (
  SELECT debit_account, credit_account, COUNT(*) AS pair_count
  FROM journal_entries
  GROUP BY debit_account, credit_account
)
SELECT je.*, pf.pair_count
FROM journal_entries je
JOIN pair_frequency pf USING (debit_account, credit_account)
WHERE pf.pair_count <= 2;

