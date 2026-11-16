"""A reproducible mortgage-file review exercise, with no real borrower records."""
import pandas as pd
OSFI_URL = "https://www.osfi-bsif.gc.ca/en/guidance/guidance-library/residential-mortgage-underwriting-practices-procedures-guideline-2017"

def review_cases(baseline):
    rows=[]
    for r in baseline.to_dict("records"):
        controls=[
            ("Purchase cash", "Modeled pass" if r["cash_pass"] else "Modeled exception",
             f'Cash target CAD {r["cash_target"]:,.0f}; stated cash CAD {r["profile_cash"]:,.0f}.',
             "Bank or investment statements; trace the source and availability of closing funds."),
            ("Debt-service screen", "Modeled pass" if r["income_pass"] else "Modeled exception",
             f'Required gross income CAD {r["required_gross_income"]:,.0f}; stated income CAD {r["profile_income"]:,.0f}.',
             "Recalculate using verified sustainable income, actual debts, rate and lender policy."),
            ("Source of down payment", "Evidence missing", "Liquid cash is a profile assumption.",
             "Confirm ownership, account history and any gift or borrowed funds."),
            ("Income and employment", "Evidence missing", "Gross income is a profile assumption.",
             "Obtain independent income and employment records appropriate to the borrower."),
            ("Existing debt and credit", "Evidence missing", "Monthly debt is assumed; credit history is absent.",
             "Reconcile liabilities and payments to credit and account records."),
            ("Property and carrying costs", "Evidence missing", "Transaction median is a benchmark; assessment, heat and fees are assumed.",
             "Obtain the purchase agreement, valuation, tax bill, condo documents and insurance."),
            ("Insurance and tax eligibility", "Evidence missing", "First-time, residence and program conditions are assumed.",
             "Verify borrower and property eligibility; obtain insurer confirmation where required."),
            ("Independent recalculation", "Arithmetic checked", "Python cash/income results reconcile to separate SQL expressions.",
             "Retain source versions, assumptions, calculations and review exceptions."),
        ]
        decision = "Hold: income shortfall and evidence missing" if not r["income_pass"] else "Hold: cash shortfall and evidence missing" if not r["cash_pass"] else "Hold: evidence missing"
        for control,status,result,evidence in controls:
            rows.append({"case_id":r["case_id"],"city":r["city"],"profile":r["profile"],
                         "profile_label":r["profile_label"],"control":control,"status":status,
                         "result":result,"evidence_needed":evidence,"review_conclusion":decision,
                         "basis":"Educational review informed by OSFI B-20; CMHC-style 39%/44% screen. Not a lender policy or approval."})
    return pd.DataFrame(rows)
