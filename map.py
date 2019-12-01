#!/usr/bin/env python3

import sys

if len(sys.argv)!=3:
    print('usage:',sys.argv[0],'input.xml output')
    sys.exit(1)

import codecs

from lxml import etree as Tree
with open(sys.argv[1]) as f:
    tree = Tree.parse(f)
    root = tree.getroot()

def decode(s):
    if s is None or s=='':
        return b'';
    return codecs.escape_decode(s)[0]

import struct, zlib
# https://stackoverflow.com/a/19174800/2640636
def write_png(buf, width, height):
    """ buf: must be bytes or a bytearray in Python3.x,
        a regular string in Python2.x.
    """

    # reverse the vertical line order and add null bytes at the start
    width_byte_4 = width * 4
    raw_data = b''.join(
        b'\x00' + buf[i:i + width_byte_4]
        for i in range(0, height * width_byte_4, width_byte_4)
    )

    def png_pack(png_tag, data):
        chunk_head = png_tag + data
        return (struct.pack("!I", len(data)) +
                chunk_head +
                struct.pack("!I", 0xFFFFFFFF & zlib.crc32(chunk_head)))

    return b''.join([
        b'\x89PNG\r\n\x1a\n',
        png_pack(b'IHDR', struct.pack("!2I5B", width, height, 8, 6, 0, 0, 0)),
        png_pack(b'IDAT', zlib.compress(raw_data, 9)),
        png_pack(b'IEND', b'')])

def add4th(s):
    return b''.join(s[i:i+3]+b'\xff' for i in range(0,len(s),3))

size = int(root.xpath('(/file/FMAP/MAPH/x)[1]')[0].text)
mapd = root.xpath('(/file/FMAP/MAPD/x)[1]')[0].text
mapd = decode(mapd)
print(len(mapd))

with open(sys.argv[2],'wb') as f:
    # f.write(mapd)
    f.write(write_png(add4th(mapd),size,size))

