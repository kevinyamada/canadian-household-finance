DROP VIEW IF EXISTS segment_yearly_changes;
CREATE VIEW segment_yearly_changes AS
SELECT quarter, "group", view, debt_income_pct, income_less_consumption,
       debt_income_pct - LAG(debt_income_pct, 4)
           OVER (PARTITION BY "group" ORDER BY quarter) AS debt_income_yoy_pp,
       income_less_consumption - LAG(income_less_consumption, 4)
           OVER (PARTITION BY "group" ORDER BY quarter) AS gap_yoy_dollars
FROM segment_history;

DROP VIEW IF EXISTS latest_segment_review;
CREATE VIEW latest_segment_review AS
SELECT quarter, "group", view, income, consumption, pension, saving,
       income_less_consumption,
       CASE WHEN income_less_consumption < 0 AND saving >= 0
            THEN 'Pension adjustment changes the sign; review saving interpretation'
            WHEN income_less_consumption >= 0 AND saving < 0
            THEN 'Pension adjustment changes the sign; review saving interpretation'
            ELSE 'No sign reversal'
       END AS reporting_note
FROM segment_history
WHERE quarter = (SELECT MAX(quarter) FROM segment_history)
  AND view IN ('Age', 'Income', 'Housing tenure');
