-- Fictional training-file checks. No real borrower evidence or approval is inferred.
DROP VIEW IF EXISTS supported_finances;
CREATE VIEW supported_finances AS
SELECT
 (SELECT SUM(CASE WHEN kind='base' THEN annual_gross ELSE 0 END) FROM income_records) AS gross_income,
 (SELECT SUM(balance-pledged) FROM fund_records) AS liquid_cash,
 (SELECT SUM(monthly_payment) FROM debt_records) AS monthly_debt;
DROP VIEW IF EXISTS stage_reconciliation;
CREATE VIEW stage_reconciliation AS
SELECT stage_id,
 required_gross_income-MAX(
   (qualifying_payment+annual_property_tax/12.0+heating+0.5*condo_fee)*12.0/0.39,
   (qualifying_payment+annual_property_tax/12.0+heating+0.5*condo_fee+monthly_debt)*12.0/0.44) AS required_income_delta,
 cash_target-(minimum_down+transfer_tax+closing_allowance+reserve) AS cash_target_delta,
 income_position-(profile_income-required_gross_income) AS income_position_delta,
 mortgage_principal-(price-down_used+insurance_premium) AS principal_delta
FROM stages;
DROP VIEW IF EXISTS finding_reconciliation;
CREATE VIEW finding_reconciliation AS
SELECT f.finding_id,
 f.supported-CASE f.field
 WHEN 'gross_income' THEN (SELECT gross_income FROM supported_finances)
 WHEN 'liquid_cash' THEN (SELECT liquid_cash FROM supported_finances)
 WHEN 'monthly_debt' THEN (SELECT monthly_debt FROM supported_finances)
 WHEN 'annual_property_tax' THEN (SELECT a.requested_price*c.assessment_ratio*c.property_tax_rate FROM application a CROSS JOIN cost_worksheet c)
 WHEN 'heating' THEN (SELECT heating FROM cost_worksheet)
 WHEN 'condo_fee' THEN (SELECT condo_fee FROM cost_worksheet)
 WHEN 'qualifying_rate_used' THEN (SELECT qualifying_rate FROM stages WHERE stage_id='corrected')
 END AS supported_delta
FROM findings f;
