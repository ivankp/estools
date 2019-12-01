#!/usr/bin/env python3

import sys, struct, json, re

if len(sys.argv)!=2:
    print('usage:',sys.argv[0],'save.ess')
    sys.exit(1)

assert (struct.calcsize('i')==4)
assert (struct.calcsize('I')==4)
assert (struct.calcsize('1s')==1)

def b2str(x):
    if isinstance(x,bytes):
        x = str(x.rstrip(b'\x00'))[2:-1]
    return x

def rb2str(x):
    if isinstance(x,bytes):
        x = str(x.lstrip(b'\x00'))[2:-1]
    return x

with open(sys.argv[1],'rb') as f:
    ess = f.read()

total_size = len(ess)
print(total_size)

with open('format.json','r') as f:
    file_format = json.load(f)

fmt_rec = file_format['records']
for key in fmt_rec:
    val = fmt_rec[key]
    if isinstance(val,str):
        fmt_rec[key] = fmt_rec[val]
fmt_flg = file_format['have_flags']

nrec = 0
class record:
    def __init__(self,tag,size):
        self.tag = tag.decode()
        self.size = size
        self.flags = None
        self.children = [ ]
        global nrec
        nrec += 1
    def write(self,f):
        f.write('<{} size="{}"'.format(self.tag,self.size))
        if self.flags is not None:
            f.write(' flags="{}"'.format(self.flags))
        f.write('>\n')
        for child in self.children:
            child.write(f)
        f.write('</{}>\n'.format(self.tag))

xml_safe_dict = [
  ('&', '&amp;'),
  ('"', '&quot;'),
  ("'", '&apos;'),
  ('<', '&lt;'),
  ('>', '&gt;')
]
def xml_safe(s):
    s = str(s)
    for c, x in xml_safe_dict:
        s = s.replace(c,x)
    return s

class attr:
    def __init__(self,fmt,val):
        self.fmt = fmt
        self.val = val
    def write(self,f):
        f.write('<x')
        if self.fmt[1] is not None:
            f.write(' name="{}"'.format(self.fmt[1]))
        f.write(' fmt="{}">'.format(self.fmt[0]))
        if len(self.val)==1:
            f.write(xml_safe(self.val[0]))
        else:
            f.write('\n')
            for x in self.val:
                f.write('<x>'+xml_safe(x)+'</x>\n')
        f.write('</x>\n')

rec_struct = struct.Struct('4sI')
flags_struct = struct.Struct('8s')

def read(data,a,b):
    recs = [ ]
    while True:
        rec = record(*rec_struct.unpack_from(data,a))
        a += 8
        if rec.tag in fmt_flg:
            rec.flags = rb2str(flags_struct.unpack_from(data,a)[0])
            a += 8
        try:
            fmts = fmt_rec[rec.tag]
        except KeyError:
            fmts = [('s',None)] if rec.flags is None else ["children"]

        end = a + rec.size
        # print('{:4} {:8} {:8} {:8} {:8}'.format(rec.tag,rec.size,a,end,b))

        last = len(fmts)-1
        for i in range(last+1):
            if fmts[i] == "children":
                rec.children.extend( read(data,a,end) )
                a = end
            else:
                fmt = fmts[i][0]
                if fmt=='s':
                    if i != last:
                        raise Exception('"s" format for not last field')
                    fmt = str(end-a) + fmt
                try:
                    rec.children.append(attr( fmts[i],
                        [ b2str(x) for x in struct.unpack_from(fmt,data,a) ]))
                except struct.error as e:
                    raise Exception(str(e)+'\nfmt: '+fmt)
                a += struct.calcsize(fmt)

        if a != end:
            raise Exception('subrecord ended at {} instead of {}'.format(a,end))
        recs.append(rec)
        if a == b: break
        elif a > b:
            raise Exception('record ended at {} instead of {}'.format(a,b))
    return recs

# tree = read(ess,0,70089+4+12)
tree = read(ess,0,total_size)

print('records in total:',nrec)
print('top level:',len(tree))

with open(re.sub('(?:\.ess)?$','.xml',sys.argv[1]),'w') as f:
    f.write('<file name="'+sys.argv[1]+'">\n')
    for node in tree:
        node.write(f)
    f.write('</file>\n')

