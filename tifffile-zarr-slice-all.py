import dask.array as da
import gc
import sys
import tifffile
import time
import zarr

path, method = sys.argv[1:]

tiff = tifffile.TiffFile(path)
assert tiff.series[0].axes == "YXS"
img = zarr.open(tiff.series[0].levels[0].pages[0].aszarr())

with profile.timestamp("begin"):
    pass

match method:
    case "dask":
        a = da.from_zarr(img)[..., 1].compute(scheduler="single-threaded")
    case "colon-colon-one":
        a = img[:, :, 1]
    case "ellipsis-one":
        a = img[..., 1]
    case _:
        raise ValueError("unknown method")
print(type(a), a.shape, a.nbytes)
time.sleep(1)
del a
gc.collect()
time.sleep(1)

with profile.timestamp("end"):
    pass
