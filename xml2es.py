#!/usr/bin/env python3

import sys
if len(sys.argv)!=3:
    print('usage:',sys.argv[0],'input.xml output.es?')
    sys.exit(1)

import re, struct, codecs
assert (struct.calcsize('i')==4)
assert (struct.calcsize('I')==4)
assert (struct.calcsize('1s')==1)
assert (struct.calcsize('b')==1)
assert (struct.calcsize('h')==2)
assert (struct.calcsize('Q')==8)
assert (struct.calcsize('q')==8)

from lxml import etree as Tree
with open(sys.argv[1]) as f:
    root = Tree.parse(f).getroot()

def decode(s):
    if s is None or s=='':
        return b'';
    return codecs.escape_decode(s)[0]

def str_enc(x):
    # return x.encode()
    return decode(x)

def char_enc(x):
    x = str_enc(x)
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

def fix(node,parent_tail=0):
    attrib = node.attrib
    if 'size' in attrib:
        size = int(attrib.get('size'))
        tail = size
        for child in node:
            tail -= fix(child,tail)
        if tail < 0:
            size -= tail
            attrib['size'] = str(size)
        size += 8
        if 'flags' in attrib:
            size += 8
        return size

    elif 'fmt' in attrib:
        children = node.getchildren()
        fmt = attrib.get('fmt')
        size = struct.calcsize(fmt)

        if re.match(r'[^0-9]*s$',fmt):
            size -= 1
            tail = parent_tail - size

            if len(children)==0:
                last = node.text
            else:
                last = children[-1].text

            last_len = len(decode(last))
            if last_len > tail: # doesn't fit
                tail = last_len
                size += last_len
            else: # fits
                size = parent_tail

            attrib['fmt'] = fmt[:-1]+'{}s'.format(tail)

        return size

def save(f,node):
    attrib = node.attrib
    if 'size' in attrib:
        size = int(attrib.get('size'))
        # print(node.tag, size)
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

    elif 'fmt' in attrib:
        children = node.getchildren()
        if len(children)==0:
            values = [ node.text ]
        else:
            values = [ child.text for child in children ]
        for i,x in enumerate(values):
            if x is None:
                values[i] = ''
        return f.write(pack(attrib.get('fmt'),values))

num_records = len(root.xpath('/file/*')) - 1
print("NumRecords:",num_records)
root.xpath('(//HEDR/*[@name="NumRecords"])[1]')[0]\
    .text = str(num_records)

print('Fixing sizes')
for record in root:
    fix(record)

# with open('tmp.xml', 'wb') as f:
#     f.write(Tree.tostring(root, pretty_print=True))

print('Writing output file')
with open(sys.argv[2],'wb') as f:
    for record in root:
        save(f,record)

