import bibtexparser
from pylatexenc.latex2text import LatexNodes2Text
import sys
import yaml

lt = LatexNodes2Text()

with open(sys.argv[1]) as f:
    db = bibtexparser.load(f)
for e in db.entries:
    for k, v in e.items():
        e[k] = lt.latex_to_text(v)
print(yaml.dump(db.entries, allow_unicode=True))
