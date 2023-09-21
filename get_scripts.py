#!/usr/bin/env python3

import sys
if len(sys.argv)!=3:
    print('usage:',sys.argv[0],'input.xml output_dir')
    sys.exit(1)

import os
os.makedirs(sys.argv[2], exist_ok=True)

from lxml import etree as Tree
with open(sys.argv[1]) as f:
    root = Tree.parse(f).getroot()

for scpt in root.xpath('/file/SCPT'):
    name = scpt.xpath('SCHD/x')[0].text
    print(name)
    with open(f'{sys.argv[2]}/{name}.mws','w') as f:
        f.write(scpt.xpath('SCTX/x')[0].text.replace(r'\r\n','\n').replace(r'\t','\t'))

