# =============================================================================
# Does RBI's Rate Cutting Cycle Actually Reach Borrowers?
# A Data Analysis of Monetary Policy Transmission in India (2014–2026)
#
# Author  : Eram Tafsir | Applied Economist & Quantitative Analyst
# Source  : Reserve Bank of India — Handbook of Statistics 2025-26
# Tables  : Table 40 (Policy Rates) | Table 59 (Structure of Interest Rates)
# =============================================================================


# %% ── SECTION 1: SETUP ──────────────────────────────────────────────────────
#
# Install any following libraries by running this in the Spyder console:
# pip install pandas numpy matplotlib openpyxl

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import warnings
warnings.filterwarnings('ignore')

# Describe Data Folder Path on Desktop:
DATA_FOLDER   = r"C:\Users\eramt\OneDrive\Desktop\Project_India\Data"
POLICY_FILE   = DATA_FOLDER + r"\Policy rates.XLSX"   # RBI Table 40
WALR_FILE     = DATA_FOLDER + r"\walr.XLSX"            # RBI Table 59
CHARTS_FOLDER = DATA_FOLDER + r"\..\Charts"            # Charts saved here

# Create the Charts folder if it does not exist yet
os.makedirs(CHARTS_FOLDER, exist_ok=True)

# ── Chart styling — clean, publication quality ───────────────────────────────
plt.rcParams.update({
    'figure.facecolor':  'white',
    'axes.facecolor':    'white',
    'axes.grid':         True,
    'grid.alpha':        0.3,
    'grid.linestyle':    '--',
    'font.family':       'sans-serif',
    'font.size':         11,
    'axes.spines.top':   False,
    'axes.spines.right': False
})


# %% ── SECTION 2: LOAD WALR DATA (Table 59) ──────────────────────────────────
# Table 59 contains annual interest rates as at end-March (end of Indian financial year)
# Actual file structure (confirmed from the RBI file):
#   - Column index 1  = financial year labels (e.g. '2014-15', '2015-16')
#   - Column index 9  = WALR on Outstanding Rupee Loans
#   - Column index 10 = WALR on Fresh Rupee Loans  ← main series we use
#   - Column index 11 = 1-Year MCLR (internal bank benchmark rate)
#   - Column index 12 = WADTDR (deposit rate — what banks pay savers)
#   - Data rows start at row index 9 (rows 0–8 are titles and column headers)
#   - Row 27 is 2026-27 which is a partial year — we exclude it (rows 9 to 26)
#
# WALR on Fresh Rupee Loans = what a new borrower pays when they take a loan
# This is only available from 2014-15 onwards andtherefore we will restrict analysis period accordingly.

# Read the full file without any header processing
walr_raw  = pd.read_excel(WALR_FILE, sheet_name='T_59', header=None)

# Extract exactly the rows and columns we need
walr_data = walr_raw.iloc[9:27, [1, 9, 10, 11, 12]].copy()
walr_data.columns = ['year', 'walr_outstanding', 'walr_fresh', 'mclr_1yr', 'wadtdr']

# Check data types of columns
print("Data types of the columns:")
print(walr_data.dtypes)

# Convert year column to string for clean matching later
walr_data['year'] = walr_data['year'].astype(str)

# Convert all rate columns to numeric
# RBI uses '--' for missing values — pd.to_numeric converts these to NaN
for col in ['walr_outstanding', 'walr_fresh', 'mclr_1yr', 'wadtdr']:
    walr_data[col] = pd.to_numeric(walr_data[col], errors='coerce')

# Keep only 2014-15 onwards (WALR on Fresh Loans not available before this)
walr_data = walr_data[walr_data['year'] >= '2014-15'].reset_index(drop=True)

print(f"✓ WALR data loaded: {len(walr_data)} financial years")
print(f"  Period: {walr_data['year'].iloc[0]} to {walr_data['year'].iloc[-1]}")
print()
print(walr_data[['year', 'walr_fresh', 'wadtdr']].to_string(index=False))


# %% ── SECTION 3: LOAD REPO RATE DATA (Table 40) ─────────────────────────────
# Table 40 contains every date on which a policy rate changed, going back to 2008.
# Two sheets — T_40(i) for older data, T_40(ii) for recent data.
# Actual file structure (confirmed from the RBI file):
#   - Column index 1 = Effective Date (already stored as datetime by Excel)
#   - Column index 3 = Repo Rate
#   - Data rows start at row index 6 (rows 0–5 are titles and headers)
#   - Rows where the rate did NOT change show '-' — we skip these rows
#
# The repo rate is event-driven — one row per rate CHANGE only.
# For each financial year end (31 March), we take the most recent rate change on or before that date. That is the rate in effect that day.

def load_repo_sheet(filepath, sheet_name):
    """
    Loads one sheet of Table 40.
    Returns a clean dataframe with 'date' and 'repo_rate' columns,
    containing only rows where the repo rate actually changed.
    """
    df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)

    # Data starts at row 6. Column 1 = date, Column 3 = repo rate
    df = df.iloc[6:, [1, 3]].copy()
    df.columns = ['date', 'repo_rate']

    # Parse dates — pandas/openpyxl reads Excel date cells as datetime
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    # Convert repo rate to numeric — '-' means no change, becomes NaN
    df['repo_rate'] = pd.to_numeric(df['repo_rate'], errors='coerce')

    # Keep only rows where BOTH date and repo rate are valid
    df = df.dropna(subset=['date', 'repo_rate'])

    return df


# Combine both sheets and sort by date
repo_raw = pd.concat(
    [load_repo_sheet(POLICY_FILE, 'T_40(i)'),
     load_repo_sheet(POLICY_FILE, 'T_40(ii)')],
    ignore_index=True
).sort_values('date').reset_index(drop=True)

print(f"✓ Repo rate loaded: {len(repo_raw)} rate-change events")
print(f"  Date range: {repo_raw['date'].iloc[0].date()} to {repo_raw['date'].iloc[-1].date()}")


# %% ── SECTION 4: EXTRACT END-MARCH REPO RATE BY FINANCIAL YEAR ──────────────
#
# The Indian financial year runs April to March. We want the repo rate in effect on 31 March of each year (the same reference date as the WALR data).
# For each end-March date, we first take all rate-change events on or before that date and then pick the last one — that is the currently active rate.

fin_years = {
    '2014-15': '2015-03-31',
    '2015-16': '2016-03-31',
    '2016-17': '2017-03-31',
    '2017-18': '2018-03-31',
    '2018-19': '2019-03-31',
    '2019-20': '2020-03-31',
    '2020-21': '2021-03-31',
    '2021-22': '2022-03-31',
    '2022-23': '2023-03-31',
    '2023-24': '2024-03-31',
    '2024-25': '2025-03-31',
    '2025-26': '2026-03-31',
}

repo_annual = []
for year_label, end_date in fin_years.items():
    target = pd.to_datetime(end_date)

    # All rate changes on or before end-March of this year
    subset = repo_raw[repo_raw['date'] <= target]

    if not subset.empty:
        # The last row = most recent change = the active rate on that date
        active_rate = float(subset.iloc[-1]['repo_rate'])
        repo_annual.append({'year': year_label, 'repo_rate': active_rate})

repo_df = pd.DataFrame(repo_annual)

print(f"✓ Repo rate extracted for {len(repo_df)} financial years")
print()
print(repo_df.to_string(index=False))


# %% ── SECTION 5: MERGE BOTH DATASETS ────────────────────────────────────────
# We join both datasets on 'year' and calculate the transmission gap.
# Transmission gap = WALR on fresh loans minus repo rate. It shows how much more than the policy rate borrowers are actually paying.
# When the gap narrows after a rate cut → transmission is working
# When the gap stays flat or rises    → banks are absorbing the cut

df = pd.merge(
    repo_df,
    walr_data[['year', 'walr_fresh', 'walr_outstanding', 'mclr_1yr', 'wadtdr']],
    on='year',
    how='inner'   # Only keep years present in both datasets
)

df['transmission_gap'] = df['walr_fresh'] - df['repo_rate']

print(f"✓ Datasets merged: {len(df)} years")
print()
print(df[['year', 'repo_rate', 'walr_fresh', 'wadtdr', 'transmission_gap']].to_string(index=False))


# %% ── CHART 1 — REPO RATE vs WALR OVER TIME ─────────────────────────────────
# Top panel : Repo rate vs WALR on fresh loans vs Deposit rate
#             Red shading = transmission gap (rate cuts never reached borrowers)
# Bottom panel: Transmission gap over time
# Rate cycles from raw RBI data file (end-March values):
#   Easing Cycle 1 : 2014-15 to 2017-18 — repo 7.50% to 6.00% (150 bps cut)
#   Easing Cycle 2 : 2018-19 to 2020-21 — repo 6.25% to 4.00% (225 bps cut)
#   Tightening     : 2021-22 to 2022-23 — repo 4.00% to 6.50% (250 bps hike)
#   Pause          : 2023-24            — repo held at 6.50%
#   Easing Cycle 3 : 2024-25 to 2025-26 — repo 6.25% to 5.25% (100 bps so far)

# Prepare data lists for plotting
years   = df['year'].tolist()
x       = list(range(len(years)))
xlabels = [y[:4] + '/' + y[-2:] for y in years]  # e.g. '2015-16' becomes '2015/16'
repo_v  = df['repo_rate'].tolist()
walr_v  = df['walr_fresh'].tolist()
wad_v   = df['wadtdr'].tolist()
gap_v   = df['transmission_gap'].tolist()

# Create two-panel figure with shared x-axis
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
fig.subplots_adjust(hspace=0.4)

# ── TOP PANEL ─────────────────────────────────────────────────────────────────

# Three interest rate lines
ax1.plot(x, repo_v, color='blue', lw=2.5, marker='o', ms=6,
         label='RBI Repo Rate — what RBI charges banks')
ax1.plot(x, walr_v, color='red', lw=2.5, marker='s', ms=6,
         label='WALR on Fresh Loans — what new borrowers actually pay')
ax1.plot(x, wad_v,  color='green', lw=1.8, marker='^', ms=5, ls='--',
         label='Deposit Rate — what banks pay savers')

# Red shading between repo rate and WALR = transmission gap
# This is the portion of rate cuts that banks did not pass on to borrowers
ax1.fill_between(x, repo_v, walr_v, alpha=0.12, color='red',
                  label='Transmission gap')

# WALR value labels directly on the chart for easy reading
for xi, yi in zip(x, walr_v):
    if not np.isnan(yi):
        ax1.annotate(f'{yi:.2f}', xy=(xi, yi),
                     xytext=(0, 10), textcoords='offset points',
                     ha='center', fontsize=8, color='red')

ax1.set_ylabel('Interest Rate (% per annum)', fontsize=12)
ax1.set_ylim(3, 12.5)
ax1.set_title(
    'RBI Policy Rate vs What Borrowers Actually Pay (2014–2026)\n'
    'The shaded area shows rate cuts that never reached borrowers',
    fontsize=13, fontweight='bold', pad=12
)
ax1.legend(loc='upper right', fontsize=9, framealpha=0.9)

# ── BOTTOM PANEL: Transmission gap over time ──────────────────────────────────
# Transmission gap = WALR minus repo rate
# Falls after a rate cut = good transmission (banks passing cut to borrowers)
# Stays flat or rises   = poor transmission (banks absorbing the cut)

gap_clean = [g if not np.isnan(g) else 0 for g in gap_v] # not changing anything here as no Nan values in gap_v

ax2.fill_between(x, gap_clean, alpha=0.3, color='red')
ax2.plot(x, gap_clean, color='red', lw=2.2, marker='o', ms=5)

# Average gap dotted line as a reference benchmark
#avg_gap = np.nanmean(gap_v)
avg_gap = np.mean(gap_clean)
ax2.axhline(y=avg_gap, color='black', ls=':', lw=1.5,
             label=f'Average gap: {avg_gap:.2f}%')

# Value labels on each data point
for xi, gi in zip(x, gap_clean):
    ax2.annotate(f'{gi:.2f}', xy=(xi, gi),
                 xytext=(0, 8), textcoords='offset points',
                 ha='center', fontsize=8.5, color='red', fontweight='bold')

ax2.set_xticks(x)
ax2.set_xticklabels(xlabels, rotation=35, ha='right', fontsize=9)
ax2.set_ylabel('Gap: WALR minus Repo Rate (%)', fontsize=12)
ax2.set_title(
    'Transmission Gap Over Time — How Much Banks Add Above the Policy Rate',
    fontsize=12, fontweight='bold'
)
ax2.legend(fontsize=10)
ax2.set_ylim(0, max(gap_clean) + 1.5)

# Data source note
fig.text(0.01, 0.01,
         'Source: Reserve Bank of India — Handbook of Statistics on the Indian Economy 2025-26, Tables 40 & 59',
         fontsize=8, color='grey')

# Save and display
chart1_path = os.path.join(CHARTS_FOLDER, 'chart1_repo_vs_walr.png')
plt.savefig(chart1_path, dpi=150, bbox_inches='tight')
plt.show()
print(f"Chart 1 saved to {chart1_path}")


# %% ── CHART 2 — PASS-THROUGH RATIOS BY EASING CYCLE ─────────────────────────
#
# For each easing cycle we compare: Pass-through ratio = (drop in WALR) / (drop in repo rate) x 100
# 100% = perfect transmission
# Above 100% = WALR fell MORE than repo (banks competed aggressively to lend)
# Below 100% = banks absorbed part of the cut
#
# Easing cycles verified from raw RBI policy rate data:
#
#   Cycle 1: Cuts from Jan 2015 to Aug 2017 — repo 8.00% to 6.00% (200 bps total)
#            In FY end-March terms: 2014-15 (7.50%) to 2017-18 (6.00%) = 150 bps
#            Note: FY start value is 7.50% because Jan 2015 cut already happened
#            before March 2015. Raw cut from peak (8.00%) was 200 bps.
#
#   Cycle 2: Cuts from Feb 2019 to May 2020 — repo 6.50% to 4.00% (250 bps total)
#            In FY end-March terms: 2018-19 (6.25%) to 2020-21 (4.00%) = 225 bps
#
#   Cycle 3: Cuts from Feb 2025 ongoing — repo 6.50% to 5.25% (125 bps so far)
#            In FY end-March terms: 2024-25 (6.25%) to 2025-26 (5.25%) = 100 bps

easing_cycles = [
    # Label uses calendar years of actual cuts (clearer than financial years)
    ('Easing Cycle 1\n(Jan 2015 – Aug 2017)', '2014-15', '2017-18'),
    ('Easing Cycle 2\n(Feb 2019 – May 2020)', '2018-19', '2020-21'),
    ('Easing Cycle 3\n(Feb 2025 – ongoing)',  '2024-25', '2025-26'),
]

results = []

for label, start_year, end_year in easing_cycles:

    start_row = df[df['year'] == start_year]
    end_row   = df[df['year'] == end_year]

    if start_row.empty or end_row.empty:
        print(f"Warning: missing data for {label}")
        continue

    repo_start = float(start_row['repo_rate'].values[0])
    repo_end   = float(end_row['repo_rate'].values[0])
    walr_start = float(start_row['walr_fresh'].values[0])
    walr_end   = float(end_row['walr_fresh'].values[0])

    # Change over the cycle — negative means rates fell (easing)
    repo_change = repo_end - repo_start
    walr_change = walr_end - walr_start

    # Pass-through ratio
    # Both changes are negative in easing cycles so ratio is positive
    # Above 100% means WALR fell MORE than the repo rate
    passthrough = (walr_change / repo_change) * 100 if repo_change != 0 else 0
    absorbed    = 100 - passthrough

    results.append({
        'label':     label,
        'repo_cut':  round(abs(repo_change) * 100),   # in basis points
        'walr_drop': round(abs(walr_change) * 100),
        'pt':        round(passthrough, 1),
        'ab':        round(absorbed, 1),
    })

    print(f"{label.replace(chr(10), ' ')}:")
    print(f"  Repo rate    : {repo_start}% to {repo_end}% = {round(abs(repo_change)*100)} bps cut")
    print(f"  WALR dropped : {walr_start:.2f}% to {walr_end:.2f}% = {round(abs(walr_change)*100)} bps")
    print(f"  Pass-through : {round(passthrough, 1)}%")
    print()

res = pd.DataFrame(results)

# ── Draw the stacked bar chart ────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(13, 7))
xr = list(range(len(res)))

# Green bar = portion of rate cut passed to borrowers
ax.bar(xr, res['pt'], 0.5, color='green', alpha=0.75,
       label='Passed to Borrowers')

# Grey bar = portion absorbed by banks, stacked on top of green
# For Cycle 1 where pass-through > 100%, absorbed is negative
# so the grey bar sits below 100% line — this is correct behaviour
ax.bar(xr, res['ab'], 0.5, bottom=res['pt'].tolist(),
       color='grey', alpha=0.75, label='Absorbed by Banks')

# Percentage labels inside each bar segment
for i, (pt, ab) in enumerate(zip(res['pt'], res['ab'])):
    # Label inside green bar
    if abs(pt) > 8:
        ax.text(i, pt / 2, f'{pt:.0f}%',
                ha='center', va='center', fontweight='bold', fontsize=14, color='white')
    # Label inside grey bar (only if visible — skip if very small)
    if abs(ab) > 8:
        ax.text(i, pt + ab / 2, f'{ab:.0f}%',
                ha='center', va='center', fontweight='bold', fontsize=13, color='white')

# Basis point annotations below each bar
for i, row in res.iterrows():
    ax.text(i, -14,
            f"RBI cut: {row['repo_cut']} bps\nBorrower got: {row['walr_drop']} bps",
            ha='center', va='top', fontsize=9.5, color='black')

# Dotted line at 100% = what perfect transmission looks like
ax.axhline(y=100, color='black', ls='--', lw=1.5, alpha=0.5,
            label='100% = Full Transmission')

ax.set_xticks(xr)
ax.set_xticklabels(res['label'], fontsize=10)
ax.set_ylim(-25, 130)
ax.set_yticks(range(0, 120, 10))
ax.set_ylabel('Share of Rate Cut (%)', fontsize=12)
ax.set_title(
    'How Much of Each RBI Rate Cut Actually Reached Borrowers?\n'
    'Pass-Through Ratio by Easing Cycle (2014–2026)',
    fontsize=13, fontweight='bold', pad=12
)
ax.legend(fontsize=10, loc='upper right')

fig.text(
    0.01, 0.01,
    'Source: Reserve Bank of India — Handbook of Statistics on the Indian Economy 2025-26, Tables 40 & 59\n'
    'Note: Pass-through = change in WALR on fresh rupee loans / change in repo rate x 100. '
    'Cycle 1 > 100% reflects aggressive bank lending post-demonetisation. '
    'Cycle 3 is ongoing as at March 2026.',
    fontsize=8, color='grey'
)

plt.tight_layout(rect=[0, 0.07, 1, 1])

chart2_path = os.path.join(CHARTS_FOLDER, 'chart2_passthrough_by_cycle.png')
plt.savefig(chart2_path, dpi=150, bbox_inches='tight')
plt.show()
print(f"Chart 2 saved to {chart2_path}")


# %% ── KEY FINDINGS SUMMARY ───────────────────────────────────────────────────

avg_pt  = res['pt'].mean()
avg_gap = df['transmission_gap'].mean()

print("=" * 65)
print("KEY FINDINGS: RBI Monetary Policy Transmission (2014–2026)")
print("=" * 65)
print(f"""
1. TRANSMISSION IS INCOMPLETE ON AVERAGE
   Across three easing cycles, only {avg_pt:.0f}% of RBI rate cuts
   reached borrowers on average. Banks absorbed the remainder.

2. TRANSMISSION GAP AVERAGED {avg_gap:.2f} PERCENTAGE POINTS
   Borrowers consistently paid ~{avg_gap:.1f}% more than the policy rate
   — reflecting credit risk premiums and deposit rate stickiness.

3. DEPOSIT RATE STICKINESS IS THE KEY CONSTRAINT
   Banks cannot cut lending rates faster than they can reprice
   deposits. The deposit rate lags both repo rate and WALR changes
   — locking in banks' cost of funds even as RBI eases.

4. THE CURRENT 2025-26 CYCLE IS STILL UNFOLDING
   With 100 bps cut so far (repo 6.25% to 5.25%), the final
   pass-through for Cycle 3 will only be known once RBI concludes
   the easing cycle and full-year WALR data is available.
""")
print("=" * 65)
print("Source : RBI Handbook of Statistics 2025-26, Tables 40 & 59")
print("Author : Eram Tafsir | github.com/eramtafsir")