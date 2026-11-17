"""Canadian home-purchase scenarios; inputs are assumptions, not loan approvals."""
from dataclasses import dataclass, replace
import math

RULE_DATE = "2026-11-16"

def number(value, name, minimum=0):
    value = float(value)
    if not math.isfinite(value) or value < minimum:
        raise ValueError(f"{name} must be finite and at least {minimum}")
    return value

@dataclass(frozen=True)
class Buyer:
    id: str
    name: str
    gross_income: float
    liquid_cash: float
    monthly_debt: float
    monthly_saving: float
    monthly_rent: float
    reserve: float = 10000
    closing_allowance: float = 4000
    heating: float = 150
    condo_fee: float = 250
    home_insurance: float = 100
    maintenance_monthly: float = 100
    first_time: bool = True
    bc_relief_eligible: bool = True

    def __post_init__(self):
        for key in ["gross_income", "liquid_cash", "monthly_debt", "monthly_saving", "monthly_rent",
                    "reserve", "closing_allowance", "heating", "condo_fee", "home_insurance", "maintenance_monthly"]:
            number(getattr(self, key), key)
        if self.gross_income <= 0:
            raise ValueError("Gross income must be positive")
        if type(self.first_time) is not bool or type(self.bc_relief_eligible) is not bool:
            raise ValueError("Eligibility flags must be explicit booleans")

PROFILES = [
    Buyer("single", "Single earner", 90000, 50000, 300, 1000, 2000),
    Buyer("couple", "Two earners", 150000, 100000, 500, 2000, 3000),
    Buyer("deposit", "Larger deposit", 120000, 250000, 0, 1500, 2500),
]

def minimum_down(price):
    p = number(price, "Price", .01)
    if p >= 1500000:
        return .20 * p
    return .05 * min(p, 500000) + .10 * max(0, p - 500000)

def insurance_premium(price, down, years=25):
    p = number(price, "Price", .01)
    d = number(down, "Down payment")
    if d > p + 1e-7:
        raise ValueError("Down payment cannot exceed price")
    if d + 1e-7 < minimum_down(p):
        raise ValueError("Down payment is below the legal minimum")
    if years not in (25, 30):
        raise ValueError("Only the documented 25- and 30-year cases are supported")
    loan = max(0, p - d)
    ltv = loan / p
    if ltv <= .80 + 1e-10:
        return 0.0
    if p >= 1500000:
        raise ValueError("Mortgage insurance requires price below CAD 1.5 million")
    rate = .028 if ltv <= .85 + 1e-10 else .031 if ltv <= .90 + 1e-10 else .04
    if years > 25:
        rate += .002
    return loan * rate

def monthly_payment(principal, annual_rate_pct, years):
    principal = number(principal, "Principal")
    rate = number(annual_rate_pct, "Rate") / 100
    years = number(years, "Years", .01)
    periods = 12 * years
    if rate == 0:
        return principal / periods
    monthly_rate = math.expm1(math.log1p(rate / 2) / 6)
    return principal * monthly_rate / (-math.expm1(-periods * math.log1p(monthly_rate)))

def balance_after(principal, annual_rate_pct, years, months=60):
    principal = number(principal, "Principal")
    months = number(months, "Months")
    if months > years * 12:
        raise ValueError("Months cannot exceed amortization")
    payment = monthly_payment(principal, annual_rate_pct, years)
    r = math.expm1(math.log1p(annual_rate_pct / 200) / 6)
    if r == 0:
        return max(0, principal - payment * months)
    growth = math.expm1(months * math.log1p(r))
    return max(0, principal * (1 + growth) - payment * growth / r)

def transfer_tax(price, province, first_time=False):
    p = number(price, "Price", .01)
    if province == "BC":
        gross = .01 * min(p, 200000) + .02 * min(max(p - 200000, 0), 1800000) + .03 * max(p - 2000000, 0) + .02 * max(p - 3000000, 0)
        if not first_time:
            relief = 0.0
        elif p <= 835000:
            relief = min(gross, 8000)
        elif p < 860000:
            relief = 8000 * (860000 - p) / 25000
        else:
            relief = 0.0
        return max(0, gross - relief), gross, relief
    if province == "NS":
        return .015 * p, .015 * p, 0.0
    raise ValueError("Only the documented BC and Halifax NS cases are supported")

def affordable_down(price, buyer, transfer, years, premium_tax_rate=0):
    """Find the largest cash-feasible down payment across discontinuous premium tiers."""
    p = number(price, "Price", .01)
    available = buyer.liquid_cash - buyer.reserve
    fixed = transfer + buyer.closing_allowance
    minimum = minimum_down(p)
    minimum_cost = minimum + fixed + premium_tax_rate * insurance_premium(p, minimum, years)
    if available + 1e-7 < minimum_cost:
        return minimum, False
    boundaries = sorted(set([minimum, *[p*x for x in [.10, .15, .20, 1] if p*x >= minimum]]))
    candidates = [minimum]
    for left, right in zip(boundaries[:-1], boundaries[1:]):
        midpoint = (left + right) / 2
        rate = insurance_premium(p, midpoint, years) / max(p - midpoint, 1e-9)
        candidate = min(right, (available - fixed - premium_tax_rate * rate * p) / (1 - premium_tax_rate * rate))
        if candidate >= left and candidate + fixed + premium_tax_rate * insurance_premium(p, candidate, years) <= available + 1e-6:
            candidates.append(candidate)
    for point in boundaries:
        if point + fixed + premium_tax_rate * insurance_premium(p, point, years) <= available + 1e-6:
            candidates.append(point)
    return min(p, max(candidates)), True

def evaluate(price, buyer, province, property_tax_rate, insured_rate, uninsured_rate,
             years=25, assessment_ratio=1.0, relief=True, use_all_cash=True):
    """Debt-service screen with purchase price used as an explicit assessment proxy."""
    p = number(price, "Price", .01)
    property_tax_rate = number(property_tax_rate, "Property tax rate")
    assessment_ratio = number(assessment_ratio, "Assessed/price ratio")
    insured_rate = number(insured_rate, "Insured rate")
    uninsured_rate = number(uninsured_rate, "Uninsured rate")
    eligible = buyer.first_time and buyer.bc_relief_eligible and relief
    tax, gross_tax, rebate = transfer_tax(p, province, eligible)
    premium_tax_rate = 0.0  # CMHC lists premium sales tax for ON, QC and SK; no selected market is in those provinces.
    minimum = minimum_down(p)
    min_premium = insurance_premium(p, minimum, years)
    min_close = minimum + tax + buyer.closing_allowance + premium_tax_rate * min_premium
    down, cash_feasible = affordable_down(p, buyer, tax, years, premium_tax_rate)
    if not use_all_cash:
        down = minimum
    premium = insurance_premium(p, down, years)
    loan = max(0, p - down) + premium
    if years == 30 and premium > 0 and not buyer.first_time:
        raise ValueError("Insured 30-year resale scenario requires a first-time buyer")
    rate = insured_rate if premium > 0 else uninsured_rate
    qualifying_rate = max(5.25, rate + 2)
    actual_payment = monthly_payment(loan, rate, years)
    stressed_payment = monthly_payment(loan, qualifying_rate, years)
    annual_tax = p * assessment_ratio * property_tax_rate
    housing_for_ratios = stressed_payment + annual_tax / 12 + buyer.heating + .5 * buyer.condo_fee
    required_income = max(housing_for_ratios / .39, (housing_for_ratios + buyer.monthly_debt) / .44) * 12 if loan > 0 else 0
    cash_gap = max(0, min_close + buyer.reserve - buyer.liquid_cash)
    income_gap = max(0, required_income - buyer.gross_income)
    cash_pass = cash_gap <= .005
    income_pass = income_gap <= .005
    barrier = "Both cash and income" if not cash_pass and not income_pass else "Cash" if not cash_pass else "Income" if not income_pass else "Within modeled limits"
    cash_spent = down + tax + buyer.closing_allowance + premium_tax_rate * premium
    balance = balance_after(loan, rate, years, 60)
    interest = max(0, actual_payment * 60 - (loan - balance))
    return {
        "price": p, "minimum_down": minimum, "transfer_tax_gross": gross_tax,
        "transfer_relief": rebate, "transfer_tax": tax, "closing_allowance": buyer.closing_allowance,
        "cash_to_close_min": min_close, "reserve": buyer.reserve, "cash_target": min_close + buyer.reserve,
        "profile_cash": buyer.liquid_cash, "cash_gap": cash_gap, "cash_pass": cash_pass,
        "down_used": down, "cash_spent": cash_spent, "cash_feasible": cash_feasible,
        "insurance_premium": premium, "mortgage_principal": loan, "contract_rate": rate,
        "qualifying_rate": qualifying_rate, "amortization_years": years,
        "monthly_mortgage": actual_payment, "qualifying_payment": stressed_payment,
        "property_tax_rate": property_tax_rate, "assessment_ratio": assessment_ratio, "annual_property_tax": annual_tax,
        "monthly_debt": buyer.monthly_debt, "heating": buyer.heating, "condo_fee": buyer.condo_fee,
        "home_insurance": buyer.home_insurance, "maintenance_monthly": buyer.maintenance_monthly,
        "modeled_monthly_outgoings": actual_payment + annual_tax/12 + buyer.heating + buyer.condo_fee + buyer.home_insurance + buyer.maintenance_monthly + buyer.monthly_debt,
        "required_gross_income": required_income, "profile_income": buyer.gross_income,
        "income_gap": income_gap, "income_pass": income_pass, "barrier": barrier,
        "gds": housing_for_ratios / (buyer.gross_income / 12),
        "tds": (housing_for_ratios + buyer.monthly_debt) / (buyer.gross_income / 12),
        "first_five_years_interest": interest, "five_year_balance": balance,
        "housing_costs_for_ratios": housing_for_ratios,
        "income_scope": "If minimum cash were available" if not cash_pass else "Uses available cash above reserve and closing costs",
        "rule_date": RULE_DATE,
        "screen_basis": "CMHC-style 39% GDS / 44% TDS screen applied consistently for comparison; uninsured lender limits may differ. Not TD policy or loan approval.",
    }

def waiting_cash(buyer, months, rent_growth):
    months = int(number(months, "Months"))
    rent_growth = number(rent_growth, "Rent growth")
    saving = sum(buyer.monthly_saving - buyer.monthly_rent * ((1 + rent_growth) ** (m / 12) - 1) for m in range(1, months + 1))
    return buyer.liquid_cash + saving
