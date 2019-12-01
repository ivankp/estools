#!/usr/bin/env python3

import sys

if len(sys.argv)!=3:
    print('usage:',sys.argv[0],'input.xml output.es?')
    sys.exit(1)

import re, struct, codecs
assert (struct.calcsize('i')==4)
assert (struct.calcsize('I')==4)
assert (struct.calcsize('1s')==1)

from lxml import etree as Tree
with open(sys.argv[1]) as f:
    tree = Tree.parse(f)
    root = tree.getroot()

def decode(s):
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
        if x!='s' and len(n)>0:
            for i in range(int(n)):
                yield x
        else:
            yield x

def pack(fmt,xs):
    return struct.pack(fmt, *(
        (type_dict[t])(x) for t,x in zip(members(fmt),xs)
    ))

struct_I = struct.Struct('I')

def save(f,node):
    attrib = node.attrib
    if 'size' in attrib:
        size = int(attrib.get('size'))
        print(node.tag, size)
        f.write(node.tag.encode('ascii'))
        f.write(struct_I.pack(size))
        flags = None
        if 'flags' in attrib:
            flags = decode(attrib.get('flags'))
            n = len(flags)
            if n<8:
                flags = b'\x00'*(8-n) + flags
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

    if 'fmt' in attrib:
        children = node.getchildren()
        if len(children)==0:
            values = [ node.text ]
        else:
            values = [ child.text for child in children ]
        for i,x in enumerate(values):
            if x is None:
                values[i] = ''
        return f.write(pack(attrib.get('fmt'),values))

# print(root.xpath('/file/TES3')[0].attrib)

with open(sys.argv[2],'wb') as f:
    for record in root:
        save(f,record)

