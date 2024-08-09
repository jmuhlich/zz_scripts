import sys
import pathlib
import pandas as pd

root = pathlib.Path('.')

rcpnl_paths = list((root / 'ashlar').rglob('*.rcpnl'))
df = pd.DataFrame({'rcpnl': rcpnl_paths})
df['parent'] = df.rcpnl.apply(lambda x: x.parent)
df['base'] = df.rcpnl.astype(str).str.extract('(Scan_.*)\.rcpnl')

metadata_paths = list((root / 'raw_data').rglob('*.metadata'))
meta = pd.DataFrame({'metadata': metadata_paths})
meta['base'] = meta.metadata.astype(str).str.extract('(Scan_.*)\.metadata')

df = pd.merge(df, meta, how='left', on='base', indicator=True)
if (df._merge == 'left_only').any():
    print("ERROR: Could not locate .metadata files for the following rcpnl files:")
    for p in df[df._merge == 'left_only'].rcpnl:
        print(p)
    sys.exit(1)
counts = df.groupby('rcpnl').size()
if (counts > 1).any():
    print("ERROR: Found multiple .metadata files for the following rcpnl files:")
    for p in counts[counts > 1].index:
        print(p)
    sys.exit(1)

df['command'] = df.apply(
    lambda r: f"# {r.rcpnl.name:>65}\ncp '{r.metadata}' '{r.parent}'",
    axis=1
)
print('\n\n'.join(df.command))
