# Does RBI's Rate Cutting Cycle Actually Reach Borrowers?
## A Data Analysis of Monetary Policy Transmission in India (2014–2026)

---

## What This Project Does

The RBI has cut its policy repo rate by a cumulative 125 basis points since February 2025.
This project answers one question using real RBI data:

**How much of that actually reaches borrowers?**

We measure this through two lenses:
1. **Overall transmission** — repo rate vs WALR on fresh loans over time (2014–2026)
2. **Pass-through ratios** — how many basis points of each easing cycle translated into actual lending rate cuts

No regression. No complex ML. Clean data analysis that tells a clear economic story.

---

## Key Findings

| Easing Cycle | RBI Cut | Borrower Received | Pass-Through |
|---|---|---|---|
| Cycle 1 (Jan 2015 – Aug 2017) | 150 bps | 173 bps | 115% |
| Cycle 2 (Feb 2019 – May 2020) | 225 bps | 177 bps | 79% |
| Cycle 3 (Feb 2025 – ongoing) | 100 bps | 95 bps | 95% |

**Average transmission gap across the period: 3.45 percentage points**
Borrowers consistently paid around 3.45% more than the policy rate throughout the period — reflecting credit risk premiums, deposit rate stickiness, and bank margin management.

**Deposit rate stickiness is the binding constraint.** Banks cannot cut lending rates faster than they can reprice their deposit liabilities — the deposit rate (WADTDR) lags both the repo rate and WALR, locking in banks' cost of funds even as RBI eases.

**Cycle 1 > 100%** reflects WALR falling more than the repo rate — likely due to abundant bank liquidity and competitive lending conditions following the demonetisation period.

---
## Data Sources

All data from a single source:

**Reserve Bank of India — Handbook of Statistics on the Indian Economy, 2025-26**
rbi.org.in/scripts/annualPublications.aspx?head=Handbook+of+Statistics+on+Indian+Economy

| File | Table | Series |
|---|---|---|
| Policy_rates.XLSX | Table 40 | Repo rate (effective date of each MPC decision) |
| walr.XLSX | Table 59 | WALR on fresh rupee loans, WALR outstanding, MCLR, WADTDR |

---
## Key Terms

- **WALR on Fresh Loans** — the average rate on new loans; what a borrower taking out a loan today actually pays
- **WADTDR** — the Weighted Average Domestic Term Deposit Rate; the average rate banks pay depositors on term deposits — the main reason banks are slow to cut lending rates
- **Pass-through ratio** — change in WALR / change in repo rate × 100
- **Transmission gap** — WALR minus repo rate; how much more than the policy rate borrowers pay

---
