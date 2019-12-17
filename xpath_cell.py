#!/usr/bin/env python3

import sys
if len(sys.argv)!=3:
    print('usage:',sys.argv[0],'input.xml output.xml')
    sys.exit(1)

from lxml import etree as Tree
with open(sys.argv[1]) as f:
    root = Tree.parse(f).getroot()

node = root.xpath('(/file/CELL/NAME/x[text()="Ald-ruhn, Hut"]/../..)')[0]

with open(sys.argv[2],'wb') as f:
    f.write(Tree.tostring(node, pretty_print=True))

