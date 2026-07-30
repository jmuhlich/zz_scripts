from ome_types.model import OME, Image, Channel, Plane, Pixels, TiffData
import pathlib
import sys
import tifffile
import uuid

# Pixel size needs to be scaled by this amount.
pixel_size_scale = 0.5

in_path = pathlib.Path(sys.argv[1])

ome = OME()
filename_template = "Scan 10x Fluor 2_w{channel}_s{series}_t1.TIF"

for i in range(49):
    filenames = [filename_template.format(series=i + 1, channel=c + 1) for c in range(4)]
    orig_metadata = [tifffile.TiffFile(f).metaseries_metadata for f in filenames]
    channels = [Channel(samples_per_pixel=1) for c in range(4)]
    tiff_data_blocks = [
        TiffData(
            uuid=TiffData.UUID(file_name=f, value=uuid.uuid4().urn),
            first_c=c,
            plane_count=1,
        )
        for c, f in enumerate(filenames)
    ]
    planes = [
        Plane(
            position_x=m['PlaneInfo']['stage-position-x'],
            position_x_unit="µm",
            position_y=m['PlaneInfo']['stage-position-y'],
            position_y_unit="µm",
            the_c=c,
            the_z=0,
            the_t=0,
        )
        for c, m in enumerate(orig_metadata)
    ]
    pi = orig_metadata[0]['PlaneInfo']
    pixels = Pixels(
        dimension_order="XYCZT",
        type="uint16",
        size_x=pi['pixel-size-x'],
        size_y=orig_metadata[0]['PlaneInfo']['pixel-size-y'],
        size_c=4,
        size_z=1,
        size_t=1,
        physical_size_x=pi['spatial-calibration-x'] * pixel_size_scale,
        physical_size_x_unit="µm",
        physical_size_y=pi['spatial-calibration-y'] * pixel_size_scale,
        physical_size_y_unit="µm",
        channels=channels,
        planes=planes,
        tiff_data_blocks=tiff_data_blocks,
    )
    image = Image(pixels=pixels)
    ome.images.append(image)

print(ome.to_xml())
