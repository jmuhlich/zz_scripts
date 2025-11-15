from ashlar.reg import ServiceFactory, OMEXMLService
import copy
from dataclasses import dataclass
import itertools
import jnius
import lxml
import numpy as np
import ome_types
import pathlib
import re
import sys
import tqdm
import uuid


@dataclass
class ImageRecord:
    path: pathlib.Path
    plate: str
    well: str
    series: int
    channel: int
    uuid: uuid.UUID
    ome: ome_types.model.Image = None


image_ids = itertools.count()
pixels_ids = itertools.count()
wellsample_idxs = itertools.count()


def merge_images(records):
    assert all(len(r.ome.pixels.channels) == 1 for r in records), "Expected 1 channel"
    assert all(len(r.ome.pixels.planes) == 1 for r in records), "Expected 1 plane"
    result = copy.deepcopy(records[0].ome)
    result.name = None
    image_id = next(image_ids)
    result.id = image_id
    result.pixels.id = next(pixels_ids)
    result.pixels.size_c = len(records)
    result.pixels.metadata_only = None
    result.pixels.channels = []
    result.pixels.planes = []

    for i, r in enumerate(records):

        channel = copy.deepcopy(r.ome.pixels.channels[0])
        channel.id = f"Channel:{image_id}:{i}"
        result.pixels.channels.append(channel)

        td_uuid = ome_types.model.TiffData.UUID(value=r.uuid.urn, file_name=str(r.path.name))
        td = ome_types.model.TiffData(uuid=td_uuid, first_c=i)
        result.pixels.tiff_data_blocks.append(td)

        plane = copy.deepcopy(r.ome.pixels.planes[0])
        plane.the_c = i
        plane.position_y *= -1
        if plane.position_x_unit == ome_types.model.UnitsLength.REFERENCEFRAME:
            plane.position_x_unit = ome_types.model.UnitsLength.MICROMETER
            plane.position_y_unit = ome_types.model.UnitsLength.MICROMETER
        result.pixels.planes.append(plane)

    return result


if __name__ == '__main__':
    ImageReader = jnius.autoclass('loci.formats.ImageReader')

    factory = ServiceFactory()
    service = jnius.cast(OMEXMLService, factory.getInstance(OMEXMLService))

    plate_acquisition = ome_types.model.PlateAcquisition()
    ome_plate = ome_types.model.Plate(rows=8, columns=12, plate_acquisitions=[plate_acquisition])
    ome = ome_types.OME(plates=[ome_plate])

    base = pathlib.Path(sys.argv[1])

    timepoint_dirs = list(base.glob('????-??-??/*/TimePoint_*'))
    if not timepoint_dirs:
        print("ERROR: Not an IXM output directory", file=sys.stderr)
        sys.exit(1)
    elif len(timepoint_dirs) > 1:
        print("ERROR: Directory has multiple rescans or timepoints", file=sys.stderr)
        sys.exit(1)
    base = timepoint_dirs[0]

    records = []
    for path in base.glob('*.tif'):
        result = re.match(r'^(.*?)_(.\d\d)_s(\d+)_w(\d)((?:_thumb)?)(.{36})\.tif$', path.name)
        if not result:
            print("SKIP: unknown filename pattern: {path.name}")
            continue
        (plate, well, series, channel, is_thumb, uuid_val) = result.groups()
        if is_thumb:
            continue
        rec = ImageRecord(path, plate, well, int(series), int(channel), uuid.UUID(uuid_val))
        records.append(rec)
    if not all(r.plate == records[0].plate for r in records[1:]):
        print("ERROR: Multiple plate/scan names encountered in filenames")
        sys.exit(1)
    ome_plate.name = records[0].plate
    records = sorted(records, key=lambda r: (r.well, r.series, r.channel))

    with tqdm.tqdm(total=len(records)) as pbar:
        for well, well_recs in itertools.groupby(records, lambda r: r.well):
            row = ord(well[0]) - ord('A')
            assert 0 <= row < 8
            column = int(well[1:]) - 1
            assert 0 <= column < 12
            ome_well = ome_types.model.Well(row=row, column=column)
            ome_plate.wells.append(ome_well)
            for series, series_recs in itertools.groupby(well_recs, lambda r: r.series):
                pbar.set_description(f"{well}/{series:02}")
                images = []
                series_recs = list(series_recs)
                for rec in series_recs:
                    pbar.update()
                    metadata = service.createOMEXMLMetadata()
                    reader = ImageReader()
                    reader.setMetadataStore(metadata)
                    reader.setId(str(rec.path))
                    ome_meta = ome_types.from_xml(service.getOMEXML(metadata))
                    assert len(ome_meta.images) == 1, "Expected 1 image"
                    rec.ome = ome_meta.images[0]

                ome_image = merge_images(series_recs)
                ome.images.append(ome_image)
                image_ref = ome_types.model.ImageRef(id=ome_image.id)
                well_sample = ome_types.model.WellSample(image_ref=image_ref, index=next(wellsample_idxs))
                ome_well.well_samples.append(well_sample)
                well_sample_ref = ome_types.model.WellSampleRef(id=well_sample.id)
                plate_acquisition.well_sample_refs.append(well_sample_ref)

    print(ome.to_xml())
