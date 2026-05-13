"""
Three-category growth rate comparison: outsourced services vs active benefits vs retiree benefits.

Data sources:
    - MPSERS contributions: FY24 ACFR Schedule of Pension Contributions (page 42)
                             FY15-FY24 actuals
    - OPEB contributions:   FY24 ACFR Schedule of OPEB Contributions (page 44)
                             FY18-FY24 actuals
    - MESSA active health:  Check register vendor data (Fund 101 + others)
    - Outsourced services:  Check register, combined of:
                              - Contract staffing (Edustaff, Professional Ed Services, etc.)
                              - DM Burr Facilities (custodial)
                              - First Group America (transportation)
    - Covered payroll:      FY24 ACFR Schedule of Pension Contributions
    - Enrollment:           FY24 ACFR Operating Indicators (page 77)

Computes:
    - CAGR for two baselines (FY18 = full pre-Covid, FY19 = Covid contracting trough)
    - Each category as % of covered payroll
    - Absolute dollar additions

The FY18 baseline is the proper pre-Covid reference. The FY19 trough makes
outsourcing look explosive due to vendor consolidation (Professional Ed Services
exited that year and Edustaff was ramping up). FY18→FY24 CAGR gives the true
structural growth rate.

Run: python compute_growth_rates.py
"""

import pandas as pd

YEARS = ['FY18', 'FY19', 'FY20', 'FY21', 'FY22', 'FY23', 'FY24', 'FY25 proj']

# In $M
DATA = {
    'MPSERS (pension)':              [22.14, 23.85, 24.92, 27.15, 30.53, 41.85, 36.62, 30.50],
    'OPEB (retiree healthcare)':     [ 5.50,  6.32,  6.39,  6.61,  6.82,  6.93,  7.26,  7.30],
    'MESSA (active health)':         [11.10, 11.10,  4.40, 14.80, 12.60, 12.70, 16.90, 15.70],
    'Contract staffing':             [ 6.16,  1.74,  1.23,  1.98,  4.01,  5.77,  5.74,  5.61],
    'DM Burr custodial':             [ 3.00,  3.15,  3.50,  4.00,  4.50,  5.00,  5.50,  5.81],
    'First Group transport':         [ 2.20,  2.93,  2.50,  2.50,  2.61,  3.29,  3.58,  4.00],
}
COVERED_PAYROLL = [73.15, 73.31, 79.54, 79.44, 83.64, 86.08, 88.37, 88.37]
ENROLLMENT      = [13034, 13061, 13073, 12723, 12519, 12540, 12447, 12276]
OPEX_TOTAL      = [150.7, 153.7, 156.9, 164.7, 172.5, 189.4, 191.5, 195.5]


def cagr(start: float, end: float, periods: int) -> float:
    return ((end / start) ** (1 / periods) - 1) * 100


def main():
    # Compose derived series
    retiree_total = [DATA['MPSERS (pension)'][i] + DATA['OPEB (retiree healthcare)'][i]
                     for i in range(len(YEARS))]
    outsourced = [DATA['Contract staffing'][i] + DATA['DM Burr custodial'][i] +
                  DATA['First Group transport'][i] for i in range(len(YEARS))]

    df = pd.DataFrame({
        'Year': YEARS,
        **DATA,
        'TOTAL Retiree Benefits': retiree_total,
        'Outsourced Services (combined)': outsourced,
    })

    print('=' * 120)
    print('ANNUAL SPEND BY CATEGORY ($M) — FY18 baseline (pre-Covid)')
    print('=' * 120)
    print()
    print(f"  {'Category':<35} " + " ".join([f"{y:>8}" for y in YEARS]))
    print('  ' + '-' * 118)
    for col in df.columns[1:]:
        vals = " ".join([f"{v:>8.2f}" for v in df[col]])
        print(f"  {col:<35} {vals}")

    print()
    print('=' * 120)
    print('GROWTH RATES — two baselines')
    print('=' * 120)
    print()
    print(f"  {'Category':<35} {'FY18':>8} {'FY19':>8} {'FY24':>8} "
          f"{'18-24 %Δ':>9} {'19-24 %Δ':>9} {'18-24 CAGR':>11} {'19-24 CAGR':>11}")
    print('  ' + '-' * 118)
    for col in ['MPSERS (pension)', 'OPEB (retiree healthcare)', 'TOTAL Retiree Benefits',
                'MESSA (active health)', 'Outsourced Services (combined)']:
        fy18, fy19, fy24 = df[col].iloc[0], df[col].iloc[1], df[col].iloc[6]
        print(f"  {col:<35} {fy18:>8.2f} {fy19:>8.2f} {fy24:>8.2f} "
              f"{((fy24/fy18-1)*100):>+8.1f}% {((fy24/fy19-1)*100):>+8.1f}% "
              f"{cagr(fy18, fy24, 6):>+10.2f}% {cagr(fy19, fy24, 5):>+10.2f}%")

    print()
    print(f"  {'-- References --':<35}")
    refs = [('Covered Payroll', COVERED_PAYROLL),
            ('Operating Expenditures', OPEX_TOTAL),
            ('Enrollment', ENROLLMENT)]
    for label, series in refs:
        fy18, fy19, fy24 = series[0], series[1], series[6]
        scale = 1 if label == 'Enrollment' else 1
        fmt = '8,' if label == 'Enrollment' else '8.2f'
        print(f"  {label:<35} {fy18:>{fmt}} {fy19:>{fmt}} {fy24:>{fmt}} "
              f"{((fy24/fy18-1)*100):>+8.1f}% {((fy24/fy19-1)*100):>+8.1f}% "
              f"{cagr(fy18, fy24, 6):>+10.2f}% {cagr(fy19, fy24, 5):>+10.2f}%")

    print()
    print('=' * 120)
    print('AS % OF COVERED PAYROLL — true cost-of-employment burden')
    print('=' * 120)
    print()
    print(f"  {'Year':<10} {'Salary':>8} {'MPSERS':>8} {'%':>6} {'OPEB':>6} {'%':>6} "
          f"{'MESSA':>7} {'%':>6} {'Outsourc':>9} {'%':>6} {'BenLoad':>9}")
    for i, y in enumerate(YEARS):
        cp = COVERED_PAYROLL[i]
        m = DATA['MPSERS (pension)'][i]
        o = DATA['OPEB (retiree healthcare)'][i]
        ms = DATA['MESSA (active health)'][i]
        ot = outsourced[i]
        benload = (m + o + ms) / cp * 100
        print(f"  {y:<10} {cp:>8.1f} {m:>8.2f} {(m/cp*100):>5.1f}% "
              f"{o:>6.2f} {(o/cp*100):>5.1f}% "
              f"{ms:>7.2f} {(ms/cp*100):>5.1f}% "
              f"{ot:>9.2f} {(ot/cp*100):>5.1f}% "
              f"{benload:>8.1f}%")

    print()
    print('=' * 120)
    print('ABSOLUTE $ ADDITIONS FY18 → FY24 (rank-ordered)')
    print('=' * 120)
    print()
    additions = []
    additions.append(('TOTAL Retiree Benefits (MPSERS+OPEB)',
                      retiree_total[6] - retiree_total[0]))
    additions.append(('Salaries (covered payroll)',
                      COVERED_PAYROLL[6] - COVERED_PAYROLL[0]))
    additions.append(('MESSA active health',
                      DATA['MESSA (active health)'][6] - DATA['MESSA (active health)'][0]))
    additions.append(('Outsourced services',
                      outsourced[6] - outsourced[0]))
    additions.sort(key=lambda x: -x[1])
    total = sum(a[1] for a in additions)
    for label, delta in additions:
        print(f"  {label:<40} +${delta:>6.2f}M  ({delta/total*100:>4.1f}% of total growth)")
    print(f"  {'-' * 40}  -----------")
    print(f"  {'Total identified growth':<40}  ${total:>6.2f}M")


if __name__ == '__main__':
    main()
