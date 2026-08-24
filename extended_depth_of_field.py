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
import dask.diagnostics as dd
import dask.array as da
import numpy as np
import skimage
import sys
import tifffile

path_in, path_out = sys.argv[1:]
tiff = tifffile.TiffFile(path_in)
img = da.from_zarr(tiff.series[0].aszarr(level=0))

def calc_edof(img):
    """Return focus-weighted sum of levels (channels) in img."""
    ## This function must remain single-threaded since dask will be calling it in parallel!
    # Normalize each level to its 90th percentile intensity.
    img_norm = img / np.quantile(img, 0.9, axis=(1, 2))[:, None, None]
    # Compute "focus quality" score as rolling-window-variance of the laplacian.
    img_laplacian = np.array([
        skimage.filters.laplace(level).astype(np.float32) for level in img_norm
    ])
    # 30x30 pixel window size is ~3 nuclei across.
    window_view = np.lib.stride_tricks.sliding_window_view(img_laplacian, (30, 30), axis=(1, 2))
    # Calling var() directly on a sliding_window_view ends up making a temporary copy of the
    # full-sized array which explodes our memory usage. Instead, we compute each 1-D slice separately 
    focus_score = np.array([[np.var(row, axis=(-2, -1)) for row in level] for level in window_view])
    # Find the best-focused level at each pixel.
    focus_labels = np.argmax(focus_score, axis=0).astype(np.uint8)
    # Apply a median filter with a ~nucleus-sized footprint to smooth out the label image.
    footprint = skimage.morphology.disk(10)
    focus_labels_f = skimage.filters.rank.median(focus_labels, footprint=footprint)
    # Sliding window gave us a smaller image. Pad it with zeros back to the original size.
    focus_labels_f = np.pad(focus_labels_f, [[15, 14], [15, 14]])
    # Convert the label image to a one-hot encoding, i.e. a binary mask for each level. We will
    # later use this image as weights for a weighted sum of the input image levels.
    weights = np.zeros(img.shape, np.float32)
    np.put_along_axis(weights, focus_labels_f[None], values=1, axis=0)
    # Apply a gaussian blur to the binary masks to implement cross-fading between levels in the
    # weighted sum, to avoid hard edges when transitioning from one level to another. The input
    # masks for each level are mutually exclusive, therefore the blurred masks will still add up to
    # 1 everywhere (up to a numerical tolerance). This can be understood by considering the
    # convolution of a gaussian (or any symmetric separable filter) with a step function and its
    # mirror image, and then the sum of those filtered signals.
    for wc in weights:
        # sigma=2.5 makes the bulk of the kernel (-/+ 2*sigma) cover one nucleus. This seems to be a
        # good size for nice transitions between levels.
        cv2.GaussianBlur(wc, (0, 0), 2.5, wc)
    # Compute weighted sum.
    res = np.clip(np.round(np.sum(img * weights, axis=0)), 0, 65535).astype(np.uint16)
    return res

img_out = da.map_overlap(
    calc_edof,
    # calc_edof takes an image encompassing all levels, so we must rechunk the input accordingly.
    img.rechunk((img.shape[0],) + img.chunksize[1:]),
    # 36 pixels was determined to be just enough to cover the edge effects of calc_edof.
    depth=(0, 36, 36),
    boundary=0,
    drop_axis=0,
    dtype=np.uint16,
)
store = da.to_zarr(img_out, path_out, mode='w', compute=False)

with dd.ProgressBar():
    store.compute()

# TODO: Copy image from zarr to compressed+pyramided ome-tiff and delete zarr.

print(f'Wrote output image to: {path_out}')
