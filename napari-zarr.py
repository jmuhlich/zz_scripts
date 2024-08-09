#!/usr/bin/env python

import dask.array as da
import napari
import pathlib
import sys
import tifffile
import zarr

#@profile
def read_pyramids(paths):
    tiffs = [tifffile.TiffFile(p) for p in paths]
    series = [t.series[0] for t in tiffs]
    pyramids = []
    for s in series:
        if s.is_pyramidal:
            za = s.aszarr()
            p = [da.from_zarr(za, component=i) for i in range(len(s.levels))]
        else:
            print(f"WARNING: Not a pyramidal TIFF: {s.parent.filename}")
            p = [s.asarray()]
            p.append(p[0][:, ::4, ::4])
            p.append(p[0][:, ::16, ::16])
        pyramids.append(p)
    return pyramids

#@profile
def build_viewer(paths, pyramids):
    viewer = napari.Viewer()
    for path, image in zip(paths, pyramids):
        fname = path.name
        names = [f"{fname} [{i}]" for i in range(image[0].shape[0])]
        viewer.add_image(image, name=names, channel_axis=0, blending="additive", contrast_limits=[0, 65535])
    for l in viewer.layers[4:]:
        l.visible = False
    return viewer

#@profile
def run_napari():
    napari.run()

paths = [pathlib.Path(p) for p in sys.argv[1:]]
pyramids = read_pyramids(paths)
viewer = build_viewer(paths, pyramids)
run_napari()
