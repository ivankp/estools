#!/usr/bin/env python3

import sys, struct, json, re

if len(sys.argv)!=2:
    print('usage:',sys.argv[0],'save.ess')
    sys.exit(1)

assert (struct.calcsize('i')==4)
assert (struct.calcsize('I')==4)
assert (struct.calcsize('1s')==1)
assert (struct.calcsize('L')==8)

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
    def __init__(self,tag,size,parent=None):
        self.tag = tag.decode()
        self.size = size
        self.flags = None
        self.children = [ ]
        self.parent = parent
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

    def fmt(self):
        tag = self.tag
        p = self.parent
        while True:
            fmt = fmt_rec.get(tag)
            if fmt is not None: return fmt
            if p is None: break
            tag = p.tag + '.' + tag
            p = p.parent
        if self.flags is None:
            return [('s',None)]
        else:
            return ["children"]

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
                f.write('<v>'+xml_safe(x)+'</v>\n')
        f.write('</x>\n')

rec_struct = struct.Struct('4sI')
flags_struct = struct.Struct('8s')

def read(data,a,b,parent=None):
    recs = [ ]
    while True:
        rec = record(*rec_struct.unpack_from(data,a),parent)
        a += 8
        if rec.tag in fmt_flg:
            rec.flags = rb2str(flags_struct.unpack_from(data,a)[0])
            a += 8
        fmts = rec.fmt()

        end = a + rec.size
        # print('{:4} {:8} {:8} {:8} {:8}'.format(rec.tag,rec.size,a,end,b))

        last = len(fmts)-1
        for i in range(last+1):
            if fmts[i] == "children":
                rec.children.extend( read(data,a,end,rec) )
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

