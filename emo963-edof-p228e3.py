# /// script
# dependencies = [
#     "opencv-python",
#     "dask",
#     "numpy",
#     "scikit-image",
#     "tifffile",
#     "zarr",
# ]
# ///

import cv2
import dask.diagnostics
import dask.array as da
import numpy as np
import skimage
import tifffile
import zarr

## Make a temp zarr copy of just the 3 DNA channels we need.
#path_in = '/n/files/HiTS/lsp-analysis/cycif-production/228-joshi-mouse-tls/p228e3_mouse_TLS_reconstruction/registration/LSP70623.ome.tif'
#tiff = tifffile.TiffFile(path_in)
#img = da.from_zarr(tiff.series[0].aszarr(level=0))
#img = img[[0, 5, 10]]
#da.to_zarr(img, 'LSP70623-dna123.zarr')

# img = da.from_zarr('LSP70623-dna123.zarr')

img = da.from_zarr(tifffile.imread('LSP70623-focus-test-crop.ome.tif', level=0, aszarr=True))

img_laplacian = da.stack([
    da.map_overlap(skimage.filters.laplace, imgc, depth=1, boundary=0).astype(np.float32)
    for imgc in img
])
img_laplacian = da.rechunk(img_laplacian, (1, 100, 100))

focus_score = da.var(
    da.lib.stride_tricks.sliding_window_view(img_laplacian, (30, 30), axis=(1, 2)),
    axis=(-2, -1),
)
focus_labels = da.argmax(focus_score, axis=0).astype(np.uint8)
focus_labels = da.rechunk(focus_labels, 1024)
footprint = skimage.morphology.disk(10)
focus_labels_f = da.map_overlap(skimage.filters.rank.median, focus_labels, depth=12, boundary=0)
focus_labels_f = da.rechunk(da.pad(focus_labels_f, [[15, 14], [15, 14]]), 1024)

def onehot(labels, num_labels, block_info=None):
    res = np.zeros((num_labels,) + labels.shape, np.float32)
    np.put_along_axis(res, labels[None], values=1, axis=0)
    return res

weights = da.map_blocks(
    onehot,
    focus_labels_f,
    len(img),
    chunks=(len(img),) + focus_labels_f.chunks,
)
weights = da.rechunk(weights, (1,) + weights.chunks[1:])

def blur(a):
    return cv2.GaussianBlur(a[0], (0, 0), 2.5)[None]

weights_f = da.map_overlap(blur, weights, depth=(0, 10, 10), boundary=0)

img_out = da.round(da.sum(img * weights_f, axis=0)).astype(np.uint16)

with dask.diagnostics.ProgressBar():
    da.to_zarr(img_out, 'LSP70623-edof.zarr', mode='w')
print('Wrote output image to: LSP70623-edof.zarr')
