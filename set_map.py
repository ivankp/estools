#!/usr/bin/env python3

import sys
if len(sys.argv)!=4:
    print('usage:',sys.argv[0],'image save.xml output.xml')
    sys.exit(1)

def encode(s):
    return str(s.rstrip(b'\x00'))[2:-1]

from PIL import Image
img = Image.open(sys.argv[1])
assert (img.size == (512,512))
pix = img.load()

pixels = b''.join(
    bytes(pix[i,j][:3])
    for j in range(512)
    for i in range(512)
)
assert (len(pixels) == 512*512*3)

from lxml import etree as Tree
with open(sys.argv[2]) as f:
    root = Tree.parse(f).getroot()

mapd = root.xpath('(/file/FMAP/MAPD/x)[1]')[0]
mapd.text = encode(pixels)

with open(sys.argv[3],'wb') as f:
    f.write(Tree.tostring(root, pretty_print=True))

