import dataclasses
import lxml.etree
import ome_types
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
align_info_raw = re.split(r'\s+', (in_path / 'AlignInfo').read_text().rstrip())
assert align_info_raw[0] == 'SAlignInfo2'
align_info = AlignInfo(*align_info_raw)

tree = lxml.etree.parse(in_path / 'ScanSpace')
points = tree.find('vPoints')
# Maps tile numbers (i.e. tif filename numbers) to point entries.
indices = [int(index.text) for index in tree.find('vSrtPrm')]

ome = ome_types.OME()
for i, index in enumerate(indices):
    point = points[index]
    channel = ome_types.model.Channel(samples_per_pixel=3)
    plane = ome_types.model.Plane(
        position_x = point.attrib['fStgX'],
        position_x_unit = 'µm',
        position_y = point.attrib['fStgY'],
        position_y_unit = 'µm',
        the_z = 0,
        the_t = 0,
        the_c = 0,
    )
    tiff_data = ome_types.model.TiffData(
        uuid=ome_types.model.TiffData.UUID(
            file_name=f'{i}.tif',
            value=uuid.uuid4().urn
        ),
    )
    pixels = ome_types.model.Pixels(
        dimension_order='XYCZT',
        type='uint8',
        size_x = align_info.tile_size_x,
        size_y = align_info.tile_size_y,
        size_z = 1,
        size_c = 3,
        size_t = 1,
        physical_size_x = align_info.pixel_size_x,
        physical_size_x_unit = 'µm',
        physical_size_y = align_info.pixel_size_y,
        physical_size_y_unit = 'µm',
        channels = [channel],
        planes = [plane],
        tiff_data_blocks = [tiff_data],
    )
    image = ome_types.model.Image(pixels=pixels)
    ome.images.append(image)

print(ome.to_xml())
