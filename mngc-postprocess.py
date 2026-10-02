# /// script
# dependencies = [
#     "numpy",
#     "scikit-image",
#     "scipy",
#     "tifffile",
# ]
# ///

# Post-process separate segmentation pass for multinucleated giant cells (GCs).
#
# Filters out common false positives from detected GCs and filters out normal
# cells that overlap GCs. Writes CSV files with cell IDs to keep for both
# normal cells and GCs.


import numpy as np
import pathlib
import scipy.ndimage as ndi
import skimage
import sys
import tifffile


from itertools import groupby
from operator import itemgetter
def collapse_consecutive(nums):
    # Sort and remove duplicates just in case
    nums = sorted(set(nums))

    # Group numbers by subtracting their index (val - idx is constant for consecutive runs)
    ranges = []
    for _, group in groupby(enumerate(nums), lambda ix: ix[0] - ix[1]):
        group = list(map(itemgetter(1), group))
        if len(group) == 1:
            ranges.append(str(group[0]))
        else:
            ranges.append(f"{group[0]}-{group[-1]}")

    return ", ".join(ranges)


if len(sys.argv) != 4:
    name = pathlib.Path(__file__).name
    print(f'Usage: {name} LSPxxxxx.ome.tif labels-standard.ome.tif labels-gc.ome.tif')
    sys.exit(1)

img_path, mask_std_path, mask_gc_path = sys.argv[1:4]

print("Loading DNA image")
img = tifffile.imread(img_path, key=0)
print("Loading standard segmentation mask")
mask_std = tifffile.imread(mask_std_path)
print("Loading giant-cell segmentation mask")
mask_gc = tifffile.imread(mask_gc_path)

def center_bias(mask, img):
    dist = ndi.distance_transform_edt(mask)
    dist /= dist.max()
    return np.sum(img * dist**2) / np.sum(img)

print("Computing standard cell image features")
props_std = skimage.measure.regionprops(mask_std, img)

print("Computing GC image features")
props_gc = skimage.measure.regionprops(mask_gc, img, extra_properties=[center_bias])

def gc_overlap_ids(p):
    return set(np.unique(mask_std[p.slice] * p.image)) - {0}

def likely_gc(p):
    return (
        # Reject hollow rings of small nuclei (common false positive in gc segmentation pass)
        (p.center_bias > 0.18)
        # Reject large dust specks and other blobs
        & (p.area < 10_000)
        # Reject various dim artifacts
        & (p.intensity_mean > 10_000)
        # Reject fibers and other elongated artifacts
        & (p.axis_major_length / p.axis_minor_length < 5)
        # Reject masks that overlap too many cells from the standard segmentation pass (bright
        # clusters of true small cells are common false positives in the gc segmentation pass)
        & (len(gc_overlap_ids(p)) < 20)
    )

props_gc_keep = [p for p in props_gc if likely_gc(p)]
cell_ids_gc_keep = [p.label for p in props_gc_keep]

cell_ids_std_discard = set.union(*(gc_overlap_ids(p) for p in props_gc_keep))
cell_ids_std_keep = set(p.label for p in props_std) - cell_ids_std_discard

print()
img_path = pathlib.Path(img_path)
stem = img_path.name.removesuffix(''.join(img_path.suffixes))

gc_keep_out_path = f'{stem}_gc_keep.csv'
print(f'Writing GC CellIDs to keep:\n    {gc_keep_out_path}')
with open(gc_keep_out_path, 'w') as f:
    f.write('CellID\n')
    f.writelines(f'{i}\n' for i in cell_ids_gc_keep)
std_keep_out_path = f'{stem}_normalcells_keep.csv'
print(f'Writing normal CellIDs to keep:\n    {std_keep_out_path}')
with open(std_keep_out_path, 'w') as f:
    f.write('CellID\n')
    f.writelines(f'{i}\n' for i in cell_ids_std_keep)
