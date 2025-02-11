import math
import numpy as np
import skimage.transform
import tifffile
import zarr


class PyramidWriter:
    """Writes a single-channel numpy array to a tiled pyramid ome-tiff."""

    def __init__(
        self, img, pixel_size, path, scale=2, tile_size=1024, peak_size=1024, verbose=False
    ):
        if img.ndim != 2:
            raise ValueError("img must have exactly 2 dimensions")
        if tile_size % 16 != 0:
            raise ValueError("tile_size must be a multiple of 16")
        self.img = img
        self.pixel_size = pixel_size
        self.path = path
        self.scale = scale
        self.tile_size = tile_size
        self.peak_size = peak_size
        self.verbose = verbose

    @property
    def base_shape(self):
        "Shape of the base level."
        return self.img.shape

    @property
    def num_levels(self):
        "Number of levels."
        factor = max(self.base_shape) / self.peak_size
        return max(math.ceil(math.log(factor, self.scale)) + 1, 1)

    @property
    def level_shapes(self):
        "Shape of all levels."
        factors = self.scale ** np.arange(self.num_levels)
        shapes = np.ceil(np.array(self.base_shape) / factors[:, None])
        return [tuple(map(int, s)) for s in shapes]

    @property
    def tile_shapes(self):
        "Tile shape of all levels."
        level_shapes = np.array(self.level_shapes)
        # The last level where we want to use the standard square tile size.
        tip_level = np.argmax(np.all(level_shapes < self.tile_size, axis=1))
        tile_shapes = [
            (self.tile_size, self.tile_size) if i <= tip_level else None
            for i in range(len(level_shapes))
        ]
        return tile_shapes

    def base_tiles(self):
        h, w = self.base_shape
        th, tw = self.tile_shapes[0]
        for y in range(0, h, th):
            for x in range(0, w, tw):
                # Returning a copy makes the array contiguous, avoiding
                # a severely unoptimized code path in ndarray.tofile.
                yield self.img[y:y+th, x:x+tw].copy()

    def subres_tiles(self, level):
        assert level >= 1
        h, w = self.level_shapes[level]
        tshape = self.tile_shapes[level] or (h, w)
        tiff = tifffile.TiffFile(self.path)
        zimg = zarr.open(tiff.aszarr(series=0, level=level-1))
        th = tshape[0] * self.scale
        tw = tshape[1] * self.scale
        for y in range(0, zimg.shape[0], th):
            for x in range(0, zimg.shape[1], tw):
                a = zimg[y:y+th, x:x+tw]
                a = skimage.transform.downscale_local_mean(
                    a, (self.scale, self.scale)
                )
                if np.issubdtype(zimg.dtype, np.integer):
                    a = np.around(a)
                a = a.astype(zimg.dtype)
                yield a

    def run(self):
        dtype = self.img.dtype
        pixel_size = self.pixel_size
        resolution_cm = 10000 / pixel_size
        metadata = {
            "Pixels": {
                "PhysicalSizeX": pixel_size, "PhysicalSizeXUnit": "\u00b5m",
                "PhysicalSizeY": pixel_size, "PhysicalSizeYUnit": "\u00b5m"
            },
        }
        with tifffile.TiffWriter(self.path, ome=True, bigtiff=True) as tiff:
            if self.verbose:
                print("Writing main image")
            tiff.write(
                data=self.base_tiles(),
                metadata=metadata,
                shape=self.level_shapes[0],
                subifds=int(self.num_levels - 1),
                dtype=dtype,
                tile=self.tile_shapes[0],
                resolution=(resolution_cm, resolution_cm, "centimeter"),
                # FIXME Propagate this from input files (especially RGB).
                photometric="minisblack",
                compression="adobe_deflate",
                predictor=True,
            )
            if self.verbose:
                print("Generating pyramid")
            for level, (shape, tile_shape) in enumerate(
                zip(self.level_shapes[1:], self.tile_shapes[1:]), 1
            ):
                if self.verbose:
                    print(f"    Level {level} ({shape[1]} x {shape[0]})")
                tiff.write(
                    data=self.subres_tiles(level),
                    shape=shape,
                    subfiletype=1,
                    dtype=dtype,
                    tile=tile_shape,
                    compression="adobe_deflate",
                    predictor=True,
                )
