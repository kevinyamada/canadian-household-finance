DROP VIEW IF EXISTS case_reconciliation;
CREATE VIEW case_reconciliation AS
SELECT case_id, city, profile, year, scenario,
       required_gross_income -
       CASE WHEN mortgage_principal <= 0 THEN 0 ELSE
         12 * MAX(
           (qualifying_payment + annual_property_tax / 12.0 + heating + condo_fee / 2.0) / 0.39,
           (qualifying_payment + annual_property_tax / 12.0 + heating + condo_fee / 2.0 + monthly_debt) / 0.44
         )
       END AS required_income_delta,
       cash_target - (minimum_down + transfer_tax + closing_allowance + reserve) AS cash_target_delta,
       cash_gap - MAX(0, cash_target-profile_cash) AS cash_gap_delta,
       income_gap - MAX(0, required_gross_income-profile_income) AS income_gap_delta,
       cash_position - (profile_cash-cash_target) AS cash_position_delta,
       income_position - (profile_income-required_gross_income) AS income_position_delta,
       mortgage_principal - MAX(0,price-down_used+insurance_premium) AS loan_delta,
       modeled_monthly_outgoings -
         (monthly_mortgage+annual_property_tax/12.0+heating+condo_fee+home_insurance+maintenance_monthly+monthly_debt)
         AS monthly_outgoings_delta
FROM purchase_cases;

DROP VIEW IF EXISTS latest_baseline;
CREATE VIEW latest_baseline AS
SELECT * FROM purchase_cases
WHERE scenario = 'baseline' AND year = (SELECT MAX(year) FROM purchase_cases);

DROP VIEW IF EXISTS barrier_summary;
CREATE VIEW barrier_summary AS
SELECT barrier, COUNT(*) AS illustrative_cases
FROM latest_baseline GROUP BY barrier;

DROP VIEW IF EXISTS cash_ready_income_short;
CREATE VIEW cash_ready_income_short AS
SELECT city, profile_label, profile_cash, cash_target, cash_position,
       profile_income, required_gross_income, income_gap
FROM latest_baseline
WHERE cash_pass = 1 AND income_pass = 0;
