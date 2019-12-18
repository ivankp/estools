#!/usr/bin/env python3

import sys
if len(sys.argv)!=4:
    print('usage:',sys.argv[0],'save.xml map.png out.png')
    sys.exit(1)

from lxml import etree as Tree
with open(sys.argv[1]) as f:
    root = Tree.parse(f).getroot()

markers = []
for cell in root.xpath('/file/CELL'):
    name = cell.xpath('NAME[1]/x')[0].text
    if not name: continue # blank name
    data = [ int(x.text) for x in cell.xpath('DATA[1]/x') ]
    if data[0] & 0x1: continue # interior
    if not (data[0] & 0x20): continue # not discovered
    print(name, data[1], data[2])
    markers.append(data[1:3])

from PIL import Image
img = Image.open(sys.argv[2])
assert (img.size == (512,512))
px = img.load()

for x,y in markers:
    x =  5*x+258
    y = -5*y+194
    for i in (-1,0,1):
        for j in (-1,0,1):
            if i==0 and j==0: continue
            px[x+i,y+j] = (202,165,96)

img.save(sys.argv[3])

