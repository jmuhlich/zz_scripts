import argparse
from ashlar import reg, transform
import ashlar.scripts.ashlar as ascript
from magicgui import magicgui
import napari
import numpy as np
import skimage
import sys
from typing import List


last_k = None

@magicgui(
    call_button="Adjust",
    log10k={
        "min": -10,
        "max": -7,
        "step": 0.01,
        "widget_type": "FloatSlider",
    },
    x={
        "min": -100,
        "max": 100,
        "step": 0.1,
        "widget_type": "FloatSlider",
    },
    y={
        "min": -100,
        "max": 100,
        "step": 0.1,
        "widget_type": "FloatSlider",
    },
    auto_call=True,
)
def adjust(log10k=-8, x=0.0, y=0.0) -> List[napari.types.LayerDataTuple]:
    global last_k, last_ac, last_bc
    k = 10 ** log10k
    # Avoid expensive transform if k is unchanged.
    if k == last_k:
        ac = last_ac
        bc = last_bc
    else:
        last_k = k
        last_ac = ac = transform.barrel_correction(a, k)
        last_bc = bc = transform.barrel_correction(b, k)
    return [
        (ac, {"name": "a"}, "points"),
        (bc, {"name": "b", "translate": (y, x)}, "points"),
    ]


parser = argparse.ArgumentParser(
    description="Visually estimate the Ashlar barrel-correction parameter",
)
parser.add_argument(
    "input", help="Bioformats-supported image file or Ashlar fileseries/filepattern string"
)
parser.add_argument(
    "tile1", type=int, help="Index of first tile to visualize (0-based)"
)
parser.add_argument(
    "tile2", type=int, help="Index of second tile to visualize (0-based)"
)
parser.add_argument(
    "-c", "--channel", type=int, default=0,
    help="Channel number to display; default: 0",
)
parser.add_argument(
    '--flip-x', default=False, action='store_true',
    help='Flip tile positions left-to-right',
)
parser.add_argument(
    '--flip-y', default=False, action='store_true',
    help='Flip tile positions top-to-bottom',
)
args = parser.parse_args()

reader = ascript.build_reader(args.input)
ascript.process_axis_flip(reader, args.flip_x, args.flip_y)

aligner = reg.EdgeAligner(reader, verbose=True)

its = aligner.intersection(args.tile1, args.tile2)
if min(its.shape) <= 1:
    print(
        f"ERROR: Tiles {args.tile1} and {args.tile2} do not overlap. Please"
        "specify adjacent tiles."
    )
    sys.exit(1)
a = reader.read(args.tile1, args.channel)
b = reader.read(args.tile2, args.channel)
a = skimage.util.img_as_float(a)
b = skimage.util.img_as_float(b)
translate = np.diff(its.offsets, axis=0)[0]
viewer = napari.Viewer()
common = dict(blending="additive", interpolation2d="bicubic")
viewer.add_image(a, name="a", translate=translate, colormap="red", **common)
viewer.add_image(b, name="b", colormap="cyan", **common)
viewer.window.add_dock_widget(adjust)
adjust()
napari.run()

print(
    "If you are satisfied with the correction you obtained, add the"
    " following to your ashlar command line:"
)
print(f"  --barrel-correction={last_k:.4g}")
