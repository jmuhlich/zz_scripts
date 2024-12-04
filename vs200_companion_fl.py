import dataclasses
import lxml.etree
import ome_types
import pandas as pd
import pathlib
import pydantic
import re
import sys
import uuid

@pydantic.validate_arguments
@dataclasses.dataclass
class AlignInfo:
    version: str
    unknown1: str
    unknown2: str
    unknown3: str
    unknown4: str
    pixel_size_x: float
    pixel_size_y: float
    tile_size_x: int
    tile_size_y: int

in_path = pathlib.Path(sys.argv[1])
align_info_raw = re.split(r"\s+", (in_path / "AlignInfo").read_text().rstrip())
assert align_info_raw[0] == "SAlignInfo2"
align_info = AlignInfo(*align_info_raw)

tree = lxml.etree.parse(in_path / "ScanSpace")
points = pd.read_xml(in_path / "ScanSpace", xpath="./vPoints/point")
# vInvSrtPrm maps point indices to field indices (.tif numbers).
points["field"] = [int(index.text) for index in tree.find("vInvSrtPrm")]
points = points.sort_values("field")
num_channels = int(tree.find("vOMs").attrib["n"])
channel_indices = list(range(num_channels))

ome = ome_types.OME()
field_groups = points.groupby("iAI", sort=False)
for _, plane_data in field_groups:
    # Ensure we have all channels and they are already sorted.
    assert list(plane_data.iOM) == channel_indices
    channels = []
    planes = []
    tiff_data_blocks = []
    for p in plane_data.itertuples():
        channels.append(ome_types.model.Channel())
        planes.append(
            ome_types.model.Plane(
                position_x = p.fStgX,
                position_x_unit = "µm",
                position_y = p.fStgY,
                position_y_unit = "µm",
                the_z = 0,
                the_t = 0,
                the_c = p.iOM,
            ),
        )
        tiff_data_blocks.append(
            ome_types.model.TiffData(
                uuid=ome_types.model.TiffData.UUID(
                    file_name=f"{p.field}.tif",
                    value=uuid.uuid4().urn,
                ),
                first_c = p.iOM,
                plane_count = 1,
            ),
        )
    pixels = ome_types.model.Pixels(
        dimension_order="XYCZT",
        type="uint16",
        size_x = align_info.tile_size_x,
        size_y = align_info.tile_size_y,
        size_z = 1,
        size_c = num_channels,
        size_t = 1,
        physical_size_x = align_info.pixel_size_x,
        physical_size_x_unit = "µm",
        physical_size_y = align_info.pixel_size_y,
        physical_size_y_unit = "µm",
        channels = channels,
        planes = planes,
        tiff_data_blocks = tiff_data_blocks,
    )
    image = ome_types.model.Image(pixels=pixels)
    ome.images.append(image)

print(ome.to_xml())
