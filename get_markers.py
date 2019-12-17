#!/usr/bin/env python3

import sys
if len(sys.argv)!=2:
    print('usage:',sys.argv[0],'input.xml')
    sys.exit(1)

from lxml import etree as Tree
with open(sys.argv[1]) as f:
    root = Tree.parse(f).getroot()

for cell in root.xpath('/file/CELL'):
    name = cell.xpath('NAME[1]/x')[0].text
    if not name: continue # blank name
    data = cell.xpath('DATA[1]/x')
    if int(data[0].text) & 0x1: continue # interior
    print(name, data[1].text, data[2].text)

