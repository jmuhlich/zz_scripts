import tifffile
import sys

path_in = sys.argv[1]
path_out_nucleus = sys.argv[2]
path_out_cell = sys.argv[3]

tiff = tifffile.TiffFile(path_in)
series = tiff.series[0]

print(f"Writing nucleus mask to: {path_out_nucleus}")
tifffile.imwrite(
    path_out_nucleus,
    series[0].asarray(),
    tile=(1024, 1024),
    compression="adobe_deflate",
    predictor=True,
    maxworkers=1,
)
print(f"Writing cell mask to: {path_out_cell}")
tifffile.imwrite(
    path_out_cell,
    series[1].asarray(),
    tile=(1024, 1024),
    compression="adobe_deflate",
    predictor=True,
    maxworkers=1,
)
