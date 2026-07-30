# Prints path and tifffile's "axes" string of first series of all tiffs passed
# on the command line

import sys
import tifffile

for p in sys.argv[1:]:
    tiff = tifffile.TiffFile(p)
    print(f'{p}\t{tiff.series[0].axes}')
