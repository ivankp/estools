#!/usr/bin/env python3

import sys
if len(sys.argv)!=2:
    print('usage:',sys.argv[0],'input.xml')
    sys.exit(1)

from lxml import etree as Tree
with open(sys.argv[1]) as f:
    root = Tree.parse(f).getroot()

for x in root.xpath('//LUAT/x'):
    print(x.text.replace(r'\\n','\n'))
    print()

