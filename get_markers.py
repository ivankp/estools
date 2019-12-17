#!/usr/bin/env python3

import sys
if len(sys.argv)!=2:
    print('usage:',sys.argv[0],'input.xml')
    sys.exit(1)

from lxml import etree as Tree
with open(sys.argv[1]) as f:
    root = Tree.parse(f).getroot()

markers = [ ]
for cell in root.xpath('/file/CELL'):
    name = cell.xpath('NAME[1]/x')[0].text
    if not name: continue # blank name
    data = [ int(x.text) for x in cell.xpath('DATA[1]/x') ]
    if data[0] & 0x1: continue # interior
    markers.append((name,data))

markers.sort()

max_len = 0
for name, data in markers:
    l = len(name)
    if l > max_len:
        max_len = l

max_len = str(max_len)
for name, data in markers:
    print(('{:'+max_len+'} {:>4} {:>4} {:0>8b}').format(
        name, data[1], data[2], data[0]))

