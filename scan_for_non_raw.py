import pathlib
import re
import sys

re_rcpnl_extra = re.compile(r'(\.rcglyph|_R40(\.stc\tmp)?|\.stc\.tmp)')
re_misc_raw = re.compile(r'(\((fld|wv) .*\.(tif|png)|info\.txt|\.xdce|\.rcjob)$')

root = pathlib.Path(sys.argv[1]).resolve()
root_name = root.name
paths = [p for p in root.rglob('*') if p.is_file()]
rcpnls = [p for p in paths if p.suffix == '.rcpnl']
rcpnl_stems = {p.stem for p in rcpnls}
for p in paths:
    stem = p.stem
    stem = re_rcpnl_extra.sub('', stem)
    if stem in rcpnl_stems:
        continue
    if re_misc_raw.search(p.name):
        continue
    print(str(root_name / p.relative_to(root)))
