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

cnts = { }

print('NPCC')
for a1 in root1.xpath('NPCC'):
    a2 = None
    sub = None
    name = None
    for b1 in a1:
        tag = b1.tag
        if a2 is None:
            assert tag == 'NAME'
            a2 = etree.Element(a1.tag)
            name = b1[0].text
            assert name is not None
            a2.attrib[tag] = name
        elif tag == 'NPDT':
            index = '{:08X}'.format(int(b1.xpath('x[@name="index"]')[0].text))
            a2.attrib['index'] = index
            cnts[name+index] = a2
        elif tag == 'NPCO':
            sub = etree.SubElement(a2,'item').attrib
            sub['name'] = b1[1].text
            sub['count'] = b1[0].text
        elif tag in ['XHLT']:
            assert sub is not None
            val = b1[0].text
            if val is not None:
                sub[tag] = val

print('CNTC')
for a1 in root1.xpath('CNTC'):
    a2 = None
    sub = None
    name = None
    for b1 in a1:
        tag = b1.tag
        if a2 is None:
            assert tag == 'NAME'
            a2 = etree.Element(a1.tag)
            name = b1[0].text
            assert name is not None
            a2.attrib[tag] = name
        elif tag == 'INDX':
            index = '{:08X}'.format(int(b1[0].text))
            a2.attrib['index'] = index
            cnts[name+index] = a2
        elif tag == 'NPCO':
            sub = etree.SubElement(a2,'item').attrib
            sub['name'] = b1[1].text
            sub['count'] = b1[0].text
        elif tag in ['XHLT']:
            assert sub is not None
            val = b1[0].text
            if val is not None:
                sub[tag] = val


print('CELL')
for a1 in root1.xpath('CELL'):
    a2 = None
    sub = None
    name = None
    for b1 in a1:
        tag = b1.tag
        if a2 is None:
            assert tag == 'NAME'
            a2 = etree.SubElement(root2,a1.tag)
            name = b1[0].text
            if name is not None:
                a2.attrib['NAME'] = name
        elif tag == 'DATA':
            if sub is None:
                flags = int(b1[0].text)
                if flags%2 != 1:
                    a2.attrib['coord'] = '{},{}'.format(b1[1].text,b1[2].text)
            else:
                sub['pos'] = coords(x.text for x in b1[0:3])
                sub['rot'] = coords(x.text for x in b1[3:6])
        elif tag == 'NAME':
            name = b1[0].text
            if name in cnts:
                sub = cnts[name]
                a2.append(sub)
                sub = sub.attrib
            else:
                sub = etree.SubElement(a2,'obj').attrib
                sub['NAME'] = name
        elif tag == 'DELE':
            # sub[tag] = b1[0].text
            sub[tag] = ''


# for cell1 in root1.xpath('CELL'):
#     cell2 = etree.SubElement(root2,'CELL')
#     first = True
#     for name in cell1.xpath('NAME'):
#         data = name.xpath('following-sibling::DATA[1]/x')
#         if first:
#             first = False
#             name = name[0].text
#             if name is not None:
#                 cell2.attrib['NAME'] = name
#             flags = int(data[0].text)
#             if flags%2 != 1:
#                 cell2.attrib['coord'] = '{},{}'.format(
#                     data[1].text, data[2].text)
#         else:
#             obj = etree.SubElement(cell2,'obj').attrib
#             obj['NAME'] = name.xpath('x')[0].text
#             obj['pos'] = coords(x.text for x in data[0:3])
#             obj['rot'] = coords(x.text for x in data[3:6])

# print("CNTCs")
# for cntc1 in root1.xpath('CNTC'):
#     cntc2 = etree.SubElement(root2,'CNTC')
#     cntc2.attrib['name'] = cntc1.xpath('NAME/x')[0].text
#     cntc2.attrib['INDX'] = cntc1.xpath('INDX/x')[0].text
#     for npco in cntc1.xpath('NPCO'):
#         obj = etree.SubElement(cntc2,'obj').attrib
#         obj['name'] = npco[1].text
#         obj['count'] = npco[0].text

ofname = re.sub(r'(\.xml)$',r'_cells\1',sys.argv[1])
print('writing',ofname)
etree.ElementTree(root2).write(
    ofname,
    pretty_print=True,
    encoding="utf-8"
)

