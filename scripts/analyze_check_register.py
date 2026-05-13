"""
Check-register vendor and function-code analyses for Troy School District.

Operates on the master workbook at
    ~/Downloads/tsd-checkregister/Troy_SD_Check_Register_FY11-FY26.xlsx

The workbook has a single "All Lines" sheet with 224K+ rows of disbursements
covering FY11-FY26. Each row has Issue Date FY, Fund, Vendor, Budget Unit,
Function Code, Account, Description, Amount.

This script produces several views used in the structural-deficit analysis:

    1. By-vendor totals, ranked, with year-by-year breakdown
    2. Edustaff line composition (Fund 122 SpEd vs Fund 101 General Fund)
    3. Out-of-district SpEd placement payments year-by-year
    4. Contract-staffing vendor history (Edustaff, Professional Ed Services,
       Educational Staffin, Safe Ed, etc.)
    5. Function-family aggregation using MI PSAM function codes 110-299

Each view prints to stdout as a fixed-width text table.

Run modes:
    python analyze_check_register.py --view vendors
    python analyze_check_register.py --view edustaff
    python analyze_check_register.py --view outofdistrict
    python analyze_check_register.py --view contracting
    python analyze_check_register.py --view functions
    python analyze_check_register.py --view all
"""

import argparse, os, sys
import pandas as pd

DEFAULT_XLSX = os.path.expanduser(
    '~/Downloads/tsd-checkregister/Troy_SD_Check_Register_FY11-FY26.xlsx'
)

# MI PSAM function code → family mapping
def func_family(fc: int) -> str:
    if 110 <= fc <= 119: return 'Instr-Basic'
    if 120 <= fc <= 129: return 'Instr-Added Needs (SpEd/Compen)'
    if 130 <= fc <= 139: return 'Instr-Adult/CommEd'
    if 210 <= fc <= 219: return 'Pupil Services'
    if 220 <= fc <= 229: return 'Instr Staff Support'
    if 230 <= fc <= 238: return 'General Admin'
    if 240 <= fc <= 249: return 'School Admin'
    if 250 <= fc <= 259: return 'Business'
    if 260 <= fc <= 269: return 'Ops & Maint'
    if 270 <= fc <= 279: return 'Transportation'
    if 280 <= fc <= 289: return 'Central'
    if 290 <= fc <= 299: return 'Athletics/Other Support'
    if 310 <= fc <= 319: return 'Community Services'
    if 410 <= fc <= 459: return 'Athletics (other fund)'
    if 510 <= fc <= 540: return 'Other Outgoing'
    if 600 <= fc <= 699: return 'Debt Service'
    if fc == 0:          return 'No Function Code'
    return f'Other ({fc})'


def load(xlsx_path: str) -> pd.DataFrame:
    print(f"Loading {xlsx_path}...", file=sys.stderr)
    df = pd.read_excel(xlsx_path, sheet_name='All Lines',
                       usecols=['Issue Date FY', 'Fund', 'Vendor Name', 'Budget Unit',
                                'Function Code', 'Account', 'Description', 'Amount'])
    df['Issue Date FY'] = df['Issue Date FY'].astype(str)
    df['Vendor Name'] = df['Vendor Name'].astype(str).str.upper()
    df['Fund'] = df['Fund'].astype(str)
    df['Account'] = df['Account'].astype(str)
    # Filter to plausible FY range
    df = df[df['Issue Date FY'].isin([f'FY{y}' for y in range(11, 27)])].copy()
    # Derive function family. Function code is typically in Budget Unit chars [6:9]
    # but ALSO populated in the parsed Function Code column.
    bu = df['Budget Unit'].astype(str)
    fc_from_bu = bu.apply(lambda x: x[6:9] if len(x) >= 9 else '')
    fc_parsed = pd.to_numeric(df['Function Code'], errors='coerce').fillna(0).astype(int)
    def pick_fc(row):
        s = row['_bu_fc']
        if s.isdigit() and len(s) == 3:
            return int(s)
        return row['_parsed_fc']
    df['_bu_fc'] = fc_from_bu
    df['_parsed_fc'] = fc_parsed
    df['FC'] = df.apply(pick_fc, axis=1)
    df['Func Family'] = df['FC'].apply(func_family)
    print(f"  Loaded {len(df):,} rows", file=sys.stderr)
    return df


def view_vendors(df: pd.DataFrame):
    """Top 30 operating-fund vendors with year-by-year breakdown."""
    op = df[df['Fund'].isin(['101', '120', '122', '129', '140'])]
    fys = [f'FY{y}' for y in range(15, 27)]
    piv = op.pivot_table(values='Amount', index='Vendor Name',
                         columns='Issue Date FY', aggfunc='sum', fill_value=0) / 1e3
    piv = piv[[c for c in fys if c in piv.columns]]
    piv['Total'] = piv.sum(axis=1)
    top = piv.nlargest(30, 'Total')
    print('\n=== Top 30 operating-fund vendors by total spend ($K) ===\n')
    print(f"  {'Vendor':<32} " + " ".join([f"{c:>7}" for c in piv.columns]))
    for v, row in top.iterrows():
        vals = " ".join([f"{int(row[c]):>7,}" for c in piv.columns])
        print(f"  {v[:32]:<32} {vals}")


def view_edustaff(df: pd.DataFrame):
    """Edustaff payments by Fund and FY."""
    fys = [f'FY{y}' for y in range(15, 27)]
    edu = df[df['Vendor Name'].str.contains('EDUSTAFF', na=False)]
    piv = edu.pivot_table(values='Amount', index='Fund',
                          columns='Issue Date FY', aggfunc='sum', fill_value=0) / 1e3
    piv = piv[[c for c in fys if c in piv.columns]]
    piv['Total'] = piv.sum(axis=1)
    print('\n=== Edustaff LLC payments by Fund and FY ($K) ===\n')
    print(f"  {'Fund':<8} " + " ".join([f"{c:>7}" for c in piv.columns]))
    for f, row in piv.sort_values('Total', ascending=False).iterrows():
        vals = " ".join([f"{int(row[c]):>7,}" for c in piv.columns])
        print(f"  Fund {f:<4} {vals}")
    totals = edu.groupby('Issue Date FY')['Amount'].sum() / 1e3
    print(f"\n  TOTAL all funds by FY:")
    for fy in fys:
        if fy in totals.index:
            print(f"    {fy}: ${int(totals[fy]):>8,}K")


def view_outofdistrict(df: pd.DataFrame):
    """Out-of-district SpEd placement payments by vendor and FY."""
    fys = [f'FY{y}' for y in range(15, 27)]
    keywords = ('OAKLAND SCHOOL', 'OAKLAND CTY', 'OAKLAND COMMUN', 'BLOOMFIELD HILLS',
                'WING LAKE', 'HURON VALLEY', 'LAMPHERE', 'UTICA SCHOOL', 'BERKLEY SCH',
                'BIRMINGHAM SCH', 'ROYAL OAK SCH', 'FARMINGTON SCH', 'WALLED LAKE',
                'SEVERIN', 'JUDSON CENTER', 'MERRILL PALMER', 'HOLY CROSS', 'SPAULDING',
                'BEAUMONT', 'JEWISH COMMUNITY', 'GRADUATION ALLIAN')
    pattern = '|'.join(keywords)
    od = df[df['Vendor Name'].str.contains(pattern, na=False, regex=True)]
    op = od[od['Fund'].isin(['101', '120', '122'])]
    piv = op.pivot_table(values='Amount', index='Vendor Name',
                         columns='Issue Date FY', aggfunc='sum', fill_value=0) / 1e3
    piv = piv[[c for c in fys if c in piv.columns]]
    piv['Total'] = piv.sum(axis=1)
    print('\n=== Out-of-district SpEd-related payments ($K) ===\n')
    print(f"  {'Vendor':<36} " + " ".join([f"{c:>7}" for c in piv.columns]))
    for v, row in piv.nlargest(15, 'Total').iterrows():
        vals = " ".join([f"{int(row[c]):>7,}" for c in piv.columns])
        print(f"  {v[:36]:<36} {vals}")
    fy_totals = op.groupby('Issue Date FY')['Amount'].sum() / 1e3
    print(f"\n  TOTAL by FY:")
    for fy in fys:
        if fy in fy_totals.index:
            print(f"    {fy}: ${int(fy_totals[fy]):>8,}K")


def view_contracting(df: pd.DataFrame):
    """All contract-staffing vendors over time."""
    fys = [f'FY{y}' for y in range(15, 27)]
    vendors = 'EDUSTAFF|PROFESSIONAL ED|TEMPORARY SCHOOL|NEXT GENERATION ENR|' \
              'E C A EDUC|SOLIANT|SUBSTITUTE TEACHER|EDUCATIONAL STAFFIN|SAFE ED LLC'
    cs = df[df['Vendor Name'].str.contains(vendors, na=False, regex=True)]
    piv = cs.pivot_table(values='Amount', index='Vendor Name',
                         columns='Issue Date FY', aggfunc='sum', fill_value=0) / 1e3
    piv = piv[[c for c in fys if c in piv.columns]]
    piv['Total'] = piv.sum(axis=1)
    print('\n=== All contract-staffing vendors ($K) ===\n')
    print(f"  {'Vendor':<36} " + " ".join([f"{c:>7}" for c in piv.columns]))
    for v, row in piv.sort_values('Total', ascending=False).iterrows():
        vals = " ".join([f"{int(row[c]):>7,}" for c in piv.columns])
        print(f"  {v[:36]:<36} {vals}")
    totals = cs.groupby('Issue Date FY')['Amount'].sum() / 1e3
    print(f"\n  TOTAL contract staffing by FY:")
    for fy in fys:
        if fy in totals.index:
            print(f"    {fy}: ${int(totals[fy]):>8,}K")


def view_functions(df: pd.DataFrame):
    """Operating-fund spend by function family by FY."""
    fys = [f'FY{y}' for y in range(15, 27)]
    op = df[df['Fund'].isin(['101', '120', '122', '129', '140'])]
    piv = op.pivot_table(values='Amount', index='Func Family',
                         columns='Issue Date FY', aggfunc='sum', fill_value=0) / 1e6
    piv = piv[[c for c in fys if c in piv.columns]]
    piv['Total'] = piv.sum(axis=1)
    print('\n=== Operating-fund spend by Function Family ($M) ===\n')
    print(f"  {'Function Family':<34} " + " ".join([f"{c:>6}" for c in piv.columns]))
    for fam, row in piv.sort_index().iterrows():
        vals = " ".join([f"{row[c]:>6.1f}" for c in piv.columns])
        print(f"  {fam[:34]:<34} {vals}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--xlsx', default=DEFAULT_XLSX,
                    help='Path to master check register xlsx')
    ap.add_argument('--view', choices=['vendors', 'edustaff', 'outofdistrict',
                                       'contracting', 'functions', 'all'],
                    default='all')
    args = ap.parse_args()
    df = load(args.xlsx)
    views = {'vendors': view_vendors, 'edustaff': view_edustaff,
             'outofdistrict': view_outofdistrict, 'contracting': view_contracting,
             'functions': view_functions}
    if args.view == 'all':
        for v in views.values():
            v(df)
    else:
        views[args.view](df)


if __name__ == '__main__':
    main()
