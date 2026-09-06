-- Revenue audit analytics: portable SQL examples (adapt date functions per database).

-- 1. Year-end cut-off population
SELECT transaction_id, customer_id, invoice_date, shipment_date,
       recognition_date, sales_amount
FROM sales
WHERE invoice_date >= '2025-12-28'
ORDER BY ABS(sales_amount) DESC;

-- 2. Revenue recognized before shipment or more than seven days after shipment
SELECT transaction_id, invoice_date, shipment_date, recognition_date, sales_amount
FROM sales
WHERE recognition_date < shipment_date
   OR julianday(recognition_date) - julianday(shipment_date) > 7;

-- 3. Material post-period returns
SELECT transaction_id, customer_id, sales_amount, return_amount,
       return_amount / NULLIF(ABS(sales_amount), 0) AS return_ratio
FROM sales
WHERE return_amount / NULLIF(ABS(sales_amount), 0) >= 0.35
ORDER BY return_ratio DESC;

-- 4. New-customer, high-value sales
SELECT transaction_id, customer_id, customer_tenure_days, sales_amount
FROM sales
WHERE customer_tenure_days < 90 AND ABS(sales_amount) >= 300000;

