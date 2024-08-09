from tifffile.tiffcomment import tiffcomment
import sys

try:
    tiff_path, = sys.argv[1:]
except ValueError:
    print("usage: fix_xmlns.py in.ome.tif [out.ome.tif]")
    print("Replace default XML namespace stripped from OME-TIFF XML")
    sys.exit(1)

xmlns = 'xmlns="http://www.openmicroscopy.org/Schemas/OME/2016-06"'
xml = tiffcomment(tiff_path)
if f" {xmlns} " in xml:
    print("Default namespace is already present in OME-XML; exiting")
    sys.exit(1)
xml = xml.replace("<OME ", f"<OME {xmlns} ", 1)
tiffcomment(tiff_path, xml)
print("Successfully injected default namespace into OME-XML")
