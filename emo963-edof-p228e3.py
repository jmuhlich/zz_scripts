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

## Make a temp zarr copy of just the 3 DNA channels we need.
#path_in = '/n/files/HiTS/lsp-analysis/cycif-production/228-joshi-mouse-tls/p228e3_mouse_TLS_reconstruction/registration/LSP70623.ome.tif'
#tiff = tifffile.TiffFile(path_in)
#img = da.from_zarr(tiff.series[0].aszarr(level=0))
#img = img[[0, 5, 10]]
#da.to_zarr(img, 'LSP70623-dna123.zarr')

img = da.from_zarr('LSP70623-dna123.zarr')

#img = img[:, 2000:12000, 20000:30000]

def calc_edof(img):
    img_norm = img / np.quantile(img, 0.9, axis=(1, 2))[:, None, None]
    img_laplacian = da.stack([
        skimage.filters.laplace(imgc).astype(np.float32) for imgc in img_norm
    ])
    img_laplacian = da.rechunk(img_laplacian, (1, 60, 60))
    focus_score = da.var(
        da.lib.stride_tricks.sliding_window_view(img_laplacian, (30, 30), axis=(1, 2)),
        axis=(-2, -1),
    )
    focus_labels = np.argmax(focus_score, axis=0).astype(np.uint8).compute()
    footprint = skimage.morphology.disk(10)
    focus_labels_f = skimage.filters.rank.median(focus_labels, footprint=footprint)
    focus_labels_f = np.pad(focus_labels_f, [[15, 14], [15, 14]])
    weights = np.zeros(img.shape, np.float32)
    np.put_along_axis(weights, focus_labels_f[None], values=1, axis=0)
    for wc in weights:
        cv2.GaussianBlur(wc, (0, 0), 2.5, wc)
    res = np.round(np.sum(img * weights, axis=0)).astype(np.uint16)
    return res

img_out = da.map_overlap(
    calc_edof,
    img.rechunk((img.shape[0],) + img.chunksize[1:]),
    depth=(0, 36, 36),
    boundary=0,
    drop_axis=0,
    dtype=np.uint16,
)
store = da.to_zarr(img_out, 'LSP70623-edof.zarr', mode='w', compute=False)
with dask.diagnostics.ProgressBar():
    store.compute(scheduler='synchronous')
print('Wrote output image to: LSP70623-edof.zarr')
