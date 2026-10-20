# /// script
# dependencies = [
#     "pandas",
#     "tifffile",
# ]
# ///

# For every cell in an mcmicro quantification table, we use the centroid
# coordinates to sample the segmentation mask image and test whether that pixel
# value matches the cell ID from the quant table. This test is meant to be
# faster than recomputing the full label quantification and doesn't require
# scikit-image at all, but it's not 100% accurate. For nucleus and whole-cell
# masks, the values should match for almost all cells (very unusual mask shapes
# can have a centroid outside the boundary of the mask but it is rare). Don't
# use this on cytoplasm-only masks as the hole in the middle will cause the
# check to fail on almost every cell.
#
# The script prints out the fraction of cells that pass the check. If the value
# is not very close to 1 there is a good chance the quantification table
# doesn't match the mask and needs to be regenerated.

import pandas as pd
import sys
import tifffile

if len(sys.argv) != 3 or not sys.argv[1].endswith('.csv') or not sys.argv[2].endswith('.tif'):
    print("Usage: mcmicro-validate-quant-masks.py quant.csv masks.tif")
    sys.exit(1)

df = pd.read_csv(sys.argv[1], usecols=['CellID', 'X_centroid', 'Y_centroid'])
labels = tifffile.imread(sys.argv[2])

df = df.round().astype(int)
df['Match'] = df.apply(lambda r: labels[r.Y_centroid, r.X_centroid] == r.CellID, axis=1)

print("Matching label fraction:", df['Match'].sum() / len(df))
