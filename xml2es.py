#!/usr/bin/env python3

import sys

if len(sys.argv)!=3:
    print('usage:',sys.argv[0],'input.xml output.es?')
    sys.exit(1)

import re, struct, codecs
assert (struct.calcsize('i')==4)
assert (struct.calcsize('I')==4)
assert (struct.calcsize('1s')==1)

# import xml.etree.ElementTree as Tree
from lxml import etree as Tree
with open(sys.argv[1]) as f:
    tree = Tree.parse(f)
    root = tree.getroot()

# attr_trans = {
#     'size': int
# }
# def attr(xs):
#     for key in xs:
#         if key in attr_trans:
#             xs[key] = attr_trans[key](xs[key])
#     return xs
#
# print(root.tag, root.attrib)
# for child in root:
#     # print(child.tag, child.attrib)
#     if len(child.attrib['flags']) != 0:
#         print(child.tag, attr(dict(child.attrib)))

def decode(s):
    # return re.sub(r'\\x([0-9A-F]{2})', lambda m: chr(int(m.group(1),16)), s)
    return codecs.escape_decode(s)[0]

def str_enc(x):
    return x.encode()

def char_enc(x):
    x = x.encode()
    if len(x)!=1: raise Exception('c must be a single byte')
    return x

type_dict = {
  'x': lambda x: None,
  'c': char_enc,
  'b': int,
  'B': int,
  '?': bool,
  'h': int,
  'H': int,
  'i': int,
  'I': int,
  'l': int,
  'L': int,
  'q': int,
  'Q': int,
  'n': int,
  'N': int,
  'e': float,
  'f': float,
  'd': float,
  's': str_enc,
  'p': str_enc,
  'P': int
}
member_re = re.compile(r'[@=<>!]*([0-9]*)(['+(''.join(type_dict.keys()))+'])')

def members(fmt):
    for m in member_re.finditer(fmt):
        n = m.group(1)
        x = m.group(2)
        if len(n)>0:
            for i in range(int(n)):
                yield x
        else:
            yield x

def pack(fmt,xs):
    # print(fmt)
    # print(xs)
    # ts = member_re.findall(fmt)
    return struct.pack(fmt, *(
        (type_dict[t])(x) for t,x in zip(members(fmt),xs)
    ))

struct_I = struct.Struct('I')

def save(f,node):
    size = node.get('size')
    if size is not None:
        size = int(size)
        print(node.tag, size)
        f.write(node.tag.encode('ascii'))
        f.write(struct_I.pack(size))
        flags = node.get('flags')
        if flags is not None:
            flags = decode(flags)
            n = len(flags)
            if n<8:
                flags = b'\x00'*n + flags
            elif n>8:
                raise Exception('flags longer than 8 bytes ({})'.format(n))
            f.write(flags)
        children_size = 0
        for child in node:
            children_size += save(f,child)
        if children_size < size:
            f.write(b'\x00'*(size-children_size))
        size += 8
        if flags is not None:
            size += 8
        return size

    fmt = node.get('fmt')
    if fmt is not None:
        children = node.getchildren()
        if len(children)==0:
            attrs = [ node.text ]
        else:
            attrs = [ child.text for child in children ]
        for i,x in enumerate(attrs):
            if x is None:
                attrs[i] = ''
        return f.write(pack(fmt,attrs))

with open(sys.argv[2],'wb') as f:
    for record in root:
        save(f,record)

