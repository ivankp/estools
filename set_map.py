#!/usr/bin/env python3

import sys
if len(sys.argv)!=4:
    print('usage:',sys.argv[0],'image save.xml output.xml')
    sys.exit(1)

xml_safe_dict = [
  ('&', '&amp;'),
  ('"', '&quot;'),
  ("'", '&apos;'),
  ('<', '&lt;'),
  ('>', '&gt;')
]
def encode(s):
    s = str(s.rstrip(b'\x00'))[2:-1]
    for c, x in xml_safe_dict:
        s = s.replace(c,x)
    return s

from PIL import Image
img = Image.open(sys.argv[1])
assert (img.size == (512,512))
pix = img.load()

pixels = b''.join(
    bytes(pix[i,j][:3])
    for i in range(512)
    for j in range(512)
)

from lxml import etree as Tree
with open(sys.argv[2]) as f:
    root = Tree.parse(f).getroot()

mapd = root.xpath('(/file/FMAP/MAPD/x)[1]')[0]
mapd.text = encode(pixels)

with open(sys.argv[3],'wb') as f:
    f.write(Tree.tostring(root, pretty_print=True))

