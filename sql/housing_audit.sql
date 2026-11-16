-- Public-accounting audit, not borrower underwriting.
DROP VIEW IF EXISTS renter_annual_audit;
CREATE VIEW renter_annual_audit AS
SELECT CAST(substr(quarter,1,4) AS INTEGER) AS year,
       COUNT(*) AS quarter_count,
       SUM(income) AS income,
       SUM(consumption) AS consumption,
       SUM(pension) AS pension,
       SUM(saving) AS reported_net_saving,
       SUM(income)-SUM(consumption) AS income_less_consumption,
       SUM(income)+SUM(pension)-SUM(consumption)-SUM(saving) AS rounding_residual
FROM segment_history
WHERE "group"='Renter'
GROUP BY substr(quarter,1,4)
HAVING COUNT(*)=4 AND COUNT(DISTINCT quarter)=4;
