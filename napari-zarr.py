#!/usr/bin/env python

import collections.abc
import dask.array as da
import napari
import pathlib
import sys
import tifffile
import zarr


class ZSLogger(collections.abc.MutableMapping):

    def __init__(self, store):
        self.store = store

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.store.close()

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def __contains__(self, key):
        return key in self.store

    def __delitem__(self, key):
        del self.store[key]

    def __setitem__(self, key, value):
        self.store[key] = value

    def __getitem__(self, key):
        print(key)
        return self.store[key]


#@profile
def read_pyramids(paths):
    tiffs = [tifffile.TiffFile(p) for p in paths]
    series = [t.series[0] for t in tiffs]
    pyramids = []
    for s in series:
        assert len(s.shape) in (2,3)
        if s.is_pyramidal:
            za = s.aszarr()
            #za = ZSLogger(za) # Enable this to log all tifffile zarr reads.
            p = [da.from_zarr(za, component=i) for i in range(len(s.levels))]
            if len(s.shape) == 2:
                p = [l[None, ...] for l in p]
        else:
            print(f"WARNING: Not a pyramidal TIFF: {s.parent.filename}")
            if len(s.shape) == 2:
                p = [s.asarray()[None, ...]]
            else:
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
