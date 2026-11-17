-- Independent checks of correct and deliberately flawed mortgage calculations.
DROP VIEW IF EXISTS calculation_audit_reconciliation;
CREATE VIEW calculation_audit_reconciliation AS
SELECT case_id,variant,
 required_gross_income-CASE WHEN qualifying_payment_used=0 AND correct_required_income=0 THEN 0
 ELSE MAX((qualifying_payment_used+housing_costs_used)*12.0/0.39,
          (qualifying_payment_used+housing_costs_used+other_debt_used)*12.0/0.44) END AS required_income_delta,
 false_pass - CASE WHEN variant!='correct' AND financial_pass=1 AND correct_financial_pass=0 THEN 1 ELSE 0 END AS false_pass_delta
FROM calculation_audit;
