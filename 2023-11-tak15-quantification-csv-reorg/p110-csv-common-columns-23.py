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
STIC_Batch3_2023/YC-Reprocess/LSP16136/quantification/LSP16136_cellRing.csv
STIC_Batch3_2023/YC-Reprocess/LSP16138/quantification/LSP16138_cellRing.csv
STIC_Batch3_2023/YC-Reprocess/LSP16141/quantification/LSP16141_cellRing.csv
STIC_Batch3_2023/YC-Reprocess/LSP16144/quantification/LSP16144_cellRing.csv
STIC_Batch3_2023/YC-Reprocess/LSP16147/quantification/LSP16147_cellRing.csv
STIC_Batch3_2023/YC-Reprocess/LSP16150/quantification/LSP16150_cellRing.csv
STIC_Batch3_2023/YC-Reprocess/LSP16153/quantification/LSP16153_cellRing.csv
STIC_Batch3_2023/YC-Reprocess/LSP16156/quantification/LSP16156_cellRing.csv
STIC_Batch3_2023/YC-Reprocess/LSP16159/quantification/LSP16159_cellRing.csv
""".split("\n")[1:-1]

standby_csv_paths = """
STIC_Batch2_2023/LSP15327/quantification/LSP15327--unmicst_cell.csv
STIC_Batch2_2023/Reprocess/LSP15331/quantification/LSP15331--unmicst_cellRing.csv
STIC_Batch2_2023/Reprocess/LSP15335/quantification/LSP15335--unmicst_cellRing.csv
STIC_Batch2_2023/Reprocess/LSP15339/quantification/LSP15339--unmicst_cellRing.csv
STIC_Batch2_2023/LSP15343/quantification/LSP15343--unmicst_cell.csv
STIC_Batch2_2023/Reprocess/LSP15347/quantification/LSP15347--unmicst_cellRing.csv
STIC_Batch2_2023/Reprocess/LSP15355/quantification/LSP15355--unmicst_cellRing.csv
STIC_Batch2_2023/Reprocess/LSP15359/quantification/LSP15359--unmicst_cellRing.csv
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
