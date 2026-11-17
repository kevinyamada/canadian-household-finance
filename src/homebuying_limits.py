"""Whole-dollar affordability thresholds across tax, insurance and rate discontinuities.

This is a debt-service comparison, not a safe-spending recommendation or approval.
Every result holds the supplied income, rates, costs and reserve fixed.
"""
from dataclasses import replace
from math import floor, ceil
from homebuying_model import evaluate, minimum_down, transfer_tax, number

TAX_BREAKS = (200000., 500000., 835000., 860000., 1500000., 2000000., 3000000.)

def _cuts(low, high, boundaries):
    """Isolate the integers on either side of each financial-rule boundary."""
    result = {int(low), int(high)}
    for point in boundaries:
        for candidate in (floor(point)-1, floor(point), ceil(point), ceil(point)+1):
            if low <= candidate <= high:
                result.add(int(candidate))
    return sorted(result)

def _interval_search(low, high, boundaries, feasible, rightmost):
    """Search each continuous piece separately; test boundary dollars explicitly."""
    if low > high:
        return None
    cuts = _cuts(low, high, boundaries)
    solutions = [p for p in cuts if feasible(p)]
    for left, right in zip(cuts[:-1], cuts[1:]):
        a, b = left+1, right-1
        if a > b:
            continue
        # Within a piece the stressed payment is affine in price/principal.
        if rightmost:
            if not feasible(a):
                continue
            if feasible(b):
                solutions.append(b)
                continue
            lo, hi = a, b
            while lo+1 < hi:
                mid = (lo+hi)//2
                if feasible(mid): lo=mid
                else: hi=mid
            solutions.append(lo)
        else:
            if not feasible(b):
                continue
            if feasible(a):
                solutions.append(a)
                continue
            lo, hi = a, b
            while lo+1 < hi:
                mid = (lo+hi)//2
                if feasible(mid): hi=mid
                else: lo=mid
            solutions.append(hi)
    return (max(solutions) if rightmost else min(solutions)) if solutions else None

def _tax(price, buyer, province, relief):
    eligible = buyer.first_time and buyer.bc_relief_eligible and relief
    return transfer_tax(price, province, eligible)[0]

def _cash_target(price, buyer, province, relief):
    return minimum_down(price)+_tax(price,buyer,province,relief)+buyer.closing_allowance+buyer.reserve

def maximum_price(buyer, province, property_tax_rate, insured_rate, uninsured_rate,
                  years=25, assessment_ratio=1., relief=True):
    """Largest feasible whole-CAD price, not a global monotonic bisection."""
    if buyer.liquid_cash < _cash_target(1,buyer,province,relief)-.005:
        return None
    # Minimum down is always at least 5% of price; this is a conservative finite upper bound.
    lo, hi = 1, max(2,ceil(20*buyer.liquid_cash)+1)
    while lo+1 < hi:
        mid=(lo+hi)//2
        if _cash_target(mid,buyer,province,relief) <= buyer.liquid_cash+.005:lo=mid
        else:hi=mid
    cash_cap=lo
    points=sorted({1.,float(cash_cap),*[b for b in TAX_BREAKS if 1<b<cash_cap]})
    boundaries=list(points)
    available=buyer.liquid_cash-buyer.reserve-buyer.closing_allowance
    # Net transfer tax is affine within these published-rule intervals.
    # Isolate loan/payoff and the 80/85/90% LTV tier/rate boundaries.
    for left,right in zip(points[:-1],points[1:]):
        if right-left < 1e-8:continue
        p1=left+(right-left)/3;p2=left+2*(right-left)/3
        t1=_tax(p1,buyer,province,relief);t2=_tax(p2,buyer,province,relief)
        slope=(t2-t1)/(p2-p1);intercept=t1-slope*p1
        for down_fraction in (.10,.15,.20,1.):
            crossing=(available-intercept)/(down_fraction+slope)
            if left <= crossing <= right:boundaries.append(crossing)
    def feasible(price):
        row=evaluate(price,buyer,province,property_tax_rate,insured_rate,uninsured_rate,
                     years=years,assessment_ratio=assessment_ratio,relief=relief)
        return row["cash_pass"] and row["income_pass"]
    price=_interval_search(1,cash_cap,boundaries,feasible,True)
    if price is not None:
        assert feasible(price)
        assert price==cash_cap or not feasible(price+1)
    return price

def minimum_cash_for_income(price, buyer, province, property_tax_rate, insured_rate,
                            uninsured_rate, years=25, assessment_ratio=1., relief=True):
    """Least total whole-CAD liquid cash that clears cash and income at a fixed price."""
    price=number(price,"Price",.01)
    fixed=_tax(price,buyer,province,relief)+buyer.closing_allowance+buyer.reserve
    low=ceil(minimum_down(price)+fixed-.005)
    high=ceil(price+fixed)
    boundaries=[fixed+price*f for f in (.10,.15,.20,1.)]
    def feasible(cash):
        row=evaluate(price,replace(buyer,liquid_cash=cash),province,property_tax_rate,insured_rate,uninsured_rate,
                     years=years,assessment_ratio=assessment_ratio,relief=relief)
        return row["cash_pass"] and row["income_pass"]
    cash=_interval_search(low,high,boundaries,feasible,False)
    assert cash is not None and feasible(cash)
    assert cash==low or not feasible(cash-1)
    return cash
