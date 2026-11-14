DROP VIEW IF EXISTS quarterly_panel;
CREATE VIEW quarterly_panel AS
SELECT h.*, p.policy_rate, p.policy_business_days, p.policy_last_date
FROM household h
LEFT JOIN policy p ON h.quarter = p.quarter;

DROP VIEW IF EXISTS recent_changes;
CREATE VIEW recent_changes AS
SELECT quarter, dsr, mortgage_dsr, other_dsr,
       dsr - LAG(dsr) OVER (ORDER BY quarter) AS dsr_qoq_pp,
       dsr - LAG(dsr, 4) OVER (ORDER BY quarter) AS dsr_yoy_pp,
       income_growth, payment_growth
FROM household;
