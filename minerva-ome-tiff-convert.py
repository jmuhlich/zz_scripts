# /// script
# dependencies = [
#     "imagecodecs",
#     "numpy",
#     "ome-types",
#     "scikit-image",
#     "tifffile>=2026.5.2",
#     "tqdm",
#     "zarr",
# ]
# ///

import sys
import argparse
import pathlib
import uuid
import numpy as np
import ome_types
import tifffile
import zarr
import tqdm


def format_shape(shape):
    return "%d x %d" % (shape[1], shape[0])


def error(path, msg):
    print(f"\nERROR: {path}: {msg}")
    sys.exit(1)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "in_path", metavar="input.ome.tif", type=pathlib.Path,
        help="OME-TIFF file to convert.",
    )
    parser.add_argument(
        "out_prefix", metavar="PREFIX",
        help="Output prefix. Output files will be named like PREFIX-foo.ome.tif",
    )
    args = parser.parse_args()
    in_path = args.in_path
    out_prefix = args.out_prefix

    tiff = tifffile.TiffFile(in_path)
    ome = ome_types.from_xml(tiff.ome_metadata)
    series = tiff.series[0]
    shape = (series.sizes["Y"], series.sizes["X"])
    dtype = series.dtype
    assert dtype == np.uint16, "Only uint16 images currently supported"
    channels = series.sizes["C"]
    img = zarr.open(series.aszarr())
    levels = len(img)
    print(f"Input image: shape={shape} levels={levels} dtype={dtype} channels={channels}")

    def tiles(level, encoder):
        imgl = img[str(level)]
        ts, tsx = imgl.chunks[1:]
        assert ts == 1024 and tsx == 1024, "Only images with 1024x1024 tiles currently supported"
        ch, cw = imgl.cdata_shape[1:]
        progress = tqdm.tqdm(
            total=imgl.nbytes, desc=f'Level {level}', unit='B', unit_scale=True
        )
        for c in range(channels):
            for j in range(ch):
                for i in range(cw):
                    tile = imgl[c, ts * j : ts * (j + 1), ts * i : ts * (i + 1)]
                    progress.update(tile.nbytes)
                    if encoder:
                        tile = encoder(tile)
                    yield tile

    def write(path, compression, encoder):
        if isinstance(compression, tuple):
            compression, compressionargs = compression
        else:
            compressionargs = None
        if encoder:
            dtype = encoder(np.array([[0]], np.uint16)).dtype
            ename = encoder.__name__
        else:
            dtype = np.dtype('uint16')
            ename = 'None'
        print(f'Output {path}: dtype={dtype} compression={compression} encoder={ename}')
        omew = ome.model_copy()
        omew.uuid = uuid.uuid4().urn
        description = omew.to_xml().encode()
        predictor = compression == 'adobe_deflate'
        photometric = 'minisblack'
        writer = tifffile.TiffWriter(path, ome=False, shaped=False, bigtiff=True)
        writer.write(
            data=tiles(0, encoder),
            shape=img['0'].shape,
            subifds=levels - 1,
            dtype=dtype,
            photometric=photometric,
            tile=img['0'].chunks[1:],
            compression=compression,
            compressionargs=compressionargs,
            predictor=predictor,
            description=description,
        )
        for level in range(1, levels):
            imgl = img[str(level)]
            writer.write(
                data=tiles(level, encoder),
                shape=imgl.shape,
                subfiletype=1,
                dtype=dtype,
                photometric=photometric,
                tile=imgl.chunks[1:],
                compression=compression,
                compressionargs=compressionargs,
                predictor=predictor,
            )
        print()

    def div256(a):
        return (a // 256).astype(np.uint8)

    def gamma3(a):
        return np.clip(np.round((a / 65536.0) ** (1/3) * 256), 0, 255).astype(np.uint8)

    print()
    #write(out_prefix + '-raw.ome.tif', None, None)
    #write(out_prefix + '-raw-zlib.ome.tif', 'adobe_deflate', None)
    #write(out_prefix + '-div256-jpeg.ome.tif', 'jpeg', div256)
    #write(out_prefix + '-gamma3-jpeg.ome.tif', ('jpeg', dict(level=90)), gamma3)
    write(out_prefix + '-gamma3-jxl.ome.tif', ('jpegxl', dict(distance=1.0)), gamma3)


if __name__ == '__main__':
    main()
