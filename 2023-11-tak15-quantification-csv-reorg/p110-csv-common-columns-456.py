import argparse
import pandas as pd
import pathlib
import re
import sys

parser = argparse.ArgumentParser()
parser.add_argument("active_base", help="Path to 110-BRCA-Mutant-Ovarian-Precursors in active storage", type=pathlib.Path)
parser.add_argument("standby_base", help="Path to 110-BRCA-Mutant-Ovarian-Precursors in standby storage", type=pathlib.Path)
parser.add_argument("output_path", help="Path to write output CSV files", type=pathlib.Path)
args = parser.parse_args()
if not args.active_base.exists():
    print(f"active_base path not found: {args.active_base}")
    sys.exit(1)
if not args.standby_base.exists():
    print(f"standby_base path not found: {args.standby_base}")
    sys.exit(1)
if not args.output_path.exists():
    print(f"output_path path not found: {args.output_path}")
    sys.exit(1)
args.active_base = args.active_base.resolve()
args.standby_base = args.standby_base.resolve()

active_csv_paths = """
STIC_Batch4_2023/YC-Reprocess/p53_signatures/LSP17762/quantification/LSP17762_cellRing.csv
STIC_Batch4_2023/YC-Reprocess/p53_signatures/LSP17802/quantification/LSP17802_cellRing.csv
STIC_Batch4_2023/YC-Reprocess/p53_signatures/LSP17818/quantification/LSP17818_cellRing.csv
STIC_Batch4_2023/YC-Reprocess/p53_signatures/LSP17822/quantification/LSP17822_cellRing.csv
STIC_Batch4_2023/YC-Reprocess/p53_signatures/LSP17850/quantification/LSP17850_cellRing.csv
STIC_Batch4_2023/YC-Reprocess/STIC_InvCa/LSP17722/quantification/LSP17722_cellRing.csv
STIC_Batch4_2023/YC-Reprocess/STIC_InvCa/LSP17726/quantification/LSP17726_cellRing.csv
STIC_Batch4_2023/YC-Reprocess/STIC_InvCa/LSP17730/quantification/LSP17730_cellRing.csv
STIC_Batch5_2023/STIC_incidental/LSP18301/quantification/LSP18301--unmicst_cellRing.csv
STIC_Batch5_2023/STIC_incidental/LSP18305/quantification/LSP18305--unmicst_cellRing.csv
STIC_Batch5_2023/STIC_incidental/LSP18309/quantification/LSP18309--unmicst_cellRing.csv
STIC_Batch5_2023/STIC_incidental/LSP18313/quantification/LSP18313--unmicst_cellRing.csv
STIC_Batch5_2023/STIC_incidental/LSP18317/quantification/LSP18317--unmicst_cellRing.csv
STIC_Batch5_2023/STIC_pilot_rerun/LSP11060/quantification/LSP11060--unmicst_cellRing.csv
STIC_Batch5_2023/STIC_pilot_rerun/LSP11064/quantification/LSP11064--unmicst_cellRing.csv
STIC_Batch5_2023/STIC_pilot_rerun/LSP11068/quantification/LSP11068--unmicst_cellRing.csv
STIC_Batch5_2023/STIC_pilot_rerun/LSP11072/quantification/LSP11072--unmicst_cellRing.csv
STIC_Batch5_2023/STIC_pilot_rerun/LSP11076/quantification/LSP11076--unmicst_cellRing.csv
STIC_Batch5_2023/STIC_pilot_rerun/LSP11088/quantification/LSP11088--unmicst_cellRing.csv
STIC_Batch6_2023/p110_incidental_p53signatures/Reprocess_quantification/LSP17734/quantification/LSP17734--unmicst_cellRing.csv
STIC_Batch6_2023/p110_incidental_p53signatures/Reprocess_quantification/LSP17786/quantification/LSP17786--unmicst_cellRing.csv
STIC_Batch6_2023/p110_incidental_p53signatures/Reprocess_quantification/LSP17766/quantification/LSP17766--unmicst_cellRing.csv
STIC_Batch6_2023/p110_incidental_p53signatures/Reprocess_quantification/LSP17758/quantification/LSP17758--unmicst_cellRing.csv
STIC_Batch6_2023/p110_incidental_p53signatures/Reprocess_quantification/LSP17790/quantification/LSP17790--unmicst_cellRing.csv
STIC_Batch6_2023/p110_STIC/LSP19416/quantification/LSP19416--unmicst_cellRing.csv
STIC_Batch6_2023/p110_STIC/LSP19420/quantification/LSP19420--unmicst_cellRing.csv
STIC_Batch6_2023/p110_STIC/LSP19412/quantification/LSP19412--unmicst_cellRing.csv
""".split("\n")[1:-1]

standby_csv_paths = """
""".split("\n")[1:-1]

renames = {
    "p-STAT1": "pSTAT1",
    "p-STAT1 ": "pSTAT1",
    "pSTAT1 ": "pSTAT1",
    "p-TBK1": "pTBK1",
    "pTBK1 ": "pTBK1",
    "CD545RO": "CD45RO",
    "PanCK_2": "PanCK",
}

active_csv_paths = [args.active_base / p for p in active_csv_paths]
standby_csv_paths = [args.standby_base / p for p in standby_csv_paths]
csv_paths = active_csv_paths + standby_csv_paths
error = False
for p in csv_paths:
    if not p.exists():
        print(f"Path to csv not found: {p}")
        error = True
if error:
    sys.exit(1)

names = pd.Series([c for p in csv_paths for c in pd.read_csv(p, nrows=0).columns])
names = names.replace(renames)
names = names[~names.str.startswith("Hoechst")]
counts = names.value_counts(sort=False)
keep_names = pd.Series(counts[counts == len(csv_paths)].index)

for p in csv_paths:
    slide_id = re.split(r"[-_]", p.name)[0]
    out_name = f"{slide_id}--unmicst_cell.csv"
    print(f"{slide_id}\n==========")
    print(f"Reading {p}")
    df = pd.read_csv(p)
    orig_cols = set(df.columns)
    df = df.rename(columns=renames)
    renamed_cols = set(df.columns)
    df = df[keep_names]
    final_cols = set(df.columns)
    if renamed_cols != orig_cols:
        print("Renaming columns:")
        for c in sorted(orig_cols - renamed_cols):
            print(f'    "{c}" -> {renames[c]}')
    if final_cols != renamed_cols:
        print("Dropping columns:")
        for c in sorted(renamed_cols - final_cols):
            print(f"    {c}")
    print(f"Writing output to file: {out_name}")
    df.to_csv(args.output_path / out_name, index=False)
    print()

print("Done!")
print(f"Output written to: {args.output_path}")
