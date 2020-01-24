#!/usr/bin/env python3

import sys
if len(sys.argv)!=2:
    print('usage:',sys.argv[0],'input.xml')
    sys.exit(1)

import re
from lxml import etree

with open(sys.argv[1]) as f:
    root1 = etree.parse(f).getroot()

root2 = etree.Element('savefile')
root2.attrib['name'] = root1.xpath('TES3/HEDR/x[4]')[0].text
root2.attrib['character'] = root1.xpath('TES3/GMDT[1]/x[4]')[0].text

def coords(vals):
    return ','.join('%g' % round(float(s),2) for s in vals)

print("CELLs")
for cell1 in root1.xpath('CELL'):
    cell2 = etree.SubElement(root2,'CELL')
    first = True
    for name in cell1.xpath('NAME'):
        data = name.xpath('following-sibling::DATA[1]/x')
        if first:
            first = False
            name = name[0].text
            if name is not None:
                cell2.attrib['NAME'] = name
            flags = int(data[0].text)
            if flags%2 != 1:
                cell2.attrib['coord'] = '{},{}'.format(
                    data[1].text, data[2].text)
        else:
            obj = etree.SubElement(cell2,'obj').attrib
            obj['NAME'] = name.xpath('x')[0].text
            obj['pos'] = coords(x.text for x in data[0:3])
            obj['rot'] = coords(x.text for x in data[3:6])

print("CNTCs")
for cntc1 in root1.xpath('CNTC'):
    cntc2 = etree.SubElement(root2,'CNTC')
    cntc2.attrib['name'] = cntc1.xpath('NAME/x')[0].text
    cntc2.attrib['INDX'] = cntc1.xpath('INDX/x')[0].text
    for npco in cntc1.xpath('NPCO'):
        obj = etree.SubElement(cntc2,'obj').attrib
        obj['name'] = npco[1].text
        obj['count'] = npco[0].text

ofname = re.sub(r'(\.xml)$',r'_cells\1',sys.argv[1])
print('writing',ofname)
etree.ElementTree(root2).write(
    ofname,
    pretty_print=True,
    encoding="utf-8"
)

