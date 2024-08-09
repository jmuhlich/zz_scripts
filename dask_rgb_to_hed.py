import numpy as np
import skimage.color.colorconv
import skimage.util

def rgb2hed(rgb):

    assert rgb.ndim == 3, "Image must have 3 dimensions"
    assert rgb.shape[2] == 3, "Image must have 3 channels (r/g/b)"
    assert rgb.dtype == np.dtype("uint8"), "Image dtype must be uint8"

    rgb = rgb / 255             # convert to float
    rgb = np.maximum(rgb, 1E-6) # avoiding log artifacts
    log_adjust = np.log(1E-6)   # used to compensate the sum above

    stains = (np.log(rgb) / log_adjust) @ skimage.color.colorconv.hed_from_rgb
    stains = np.maximum(stains, 0)

    return stains
