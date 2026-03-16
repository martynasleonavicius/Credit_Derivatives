# CDS spread calculator
A Python implementation of Credit Default Swap (CDS) spread calculator for real companies, using live US Treasury yield curve data and market bond prices.
The methodology follows **John C. Hull's *Options, Futures, and Other Derivatives*, 7th edition** - specifically chapters 22 (default probabilities) and 23 (CDS pricing).

---

## What it does
Given a company's bond data, the project:

1. Fetches the current US Treasury zero-yield curve from [FRED](https://fred.stlouisfed.org/)
2. Bootstraps a bond spread by solving for the rate that prices the bond correctly against its market value
3. Derives a hazard rate from the spread, assuming spread reflects default risk only
4. Calculates CDS contract's spread spanning from today to the bond's maturity, accounting for:
    - Scheduled premium payments (survival-weighted)
    - Expected default payouts (with a 40% recovery rate)
    - Accrued premium payments in the event of a mid-year default



Two companies are currently supported: **Petroleos Mexicanos** and **Mars INC DEL**, with bond data last updated on 12/03/2026.

---

## Example output:
```
Spread is: 76.343 basis points (bps) for Mars INC DEL and 277.866  basis points (bps) for Petroleos Mexicanos (PEMEX).
```

---
## Project structure
```
├── yield_curve_getter.py   # Fetches live Treasury yields from FRED
├── spread_calculator.py    # Bootstraps bond spread from market price
├── cds_company_spread.py   # Finds CDS contract's spread
└── cds_simple_spread.py    # Standalone simplified demo (flat curve, constant default probability)
```
---
## Installation
```bash
pip install numpy pandas scipy
```
No API key is required - yield data is pulled directly from FRED's public CSV endpoint.

## Usage
To price a CDS for one of the supported companies, open `cds_company_pricer.py` and set `company_name` at the top of the `__main__` block:

```python
company_name = "Mars INC DEL"        # or "Petroleos Mexicanos"
```

Then run:

```bash
python cds_company_pricer.py
```

To explore the simplified model with a flat yield curve and constant default probability, run:

```bash
python cds_simple_pricer.py
```

---

## Adding a new company
To price a CDS for a different company, add its bond data to the `bonds` dictionary in `spread_calculator.py`:

```python
bonds = {
    "Your Company": [COUPON_RATE, 'MM/DD/YYYY', LAST_PRICE, YIELD, 'MM/DD/YYYY'],
    #                 e.g. 5.0       maturity      market px  ytm    last trade date
}
```

Coupons are assumed to be paid annually. Prices should be quoted per 100 face value (clean/dirty conventions are handled internally). The YIELD and last trade date fields are stored for reference but are not used in the calculation.

---

## Assumptions

- Annual coupon payments
- Actual/365 day-count convention
- Defaults can only occur at the midpoint of each payment period
- Bond spread reflects default risk only (no liquidity or tax premium)
- Recovery rate: 40%
- Treasury yields are used as the risk-free rate proxy
- Yields beyond 30 years are capped at the 30-year rate; yields under 6 months use the 6-month rate

---

## Limitations

---

- Bond data is hardcoded and time-sensitive - results are most meaningful when run close to the last trade date
- The FRED data only goes out to 30 years; longer-dated bonds will use the 30-year rate for all payments beyond that horizon
- A single flat hazard rate is assumed across the life of the contract

---

## References

Hull, J. C. (2009). Options, Futures, and Other Derivatives (7th ed.). Pearson Prentice Hall.
- Chapter 22: Credit Risk
- Chapter 23: Credit Derivatives
