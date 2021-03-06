#!/usr/bin/env python3
# https://www.mwmythicmods.com/argent/tech/es_format.html
# https://www.mwmythicmods.com/tutorials/MorrowindESPFormat.html

import sys, struct, json, re

flags = { x: False for x in ['v'] }
for i,arg in enumerate(sys.argv[1:],1):
    if not arg.startswith('-'): continue
    a = arg[1:]
    if a in flags:
        flags[a] = True
        print('set',sys.argv.pop(i))

if len(sys.argv)!=2 and len(sys.argv)!=3:
    print('usage:',sys.argv[0],'save.ess [output.xml]')
    sys.exit(1)

assert (struct.calcsize('i')==4)
assert (struct.calcsize('I')==4)
assert (struct.calcsize('1s')==1)
assert (struct.calcsize('b')==1)
assert (struct.calcsize('h')==2)
assert (struct.calcsize('Q')==8)
assert (struct.calcsize('q')==8)

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

    def write(self,f,indent=0):
        indent_str = ' '*indent
        f.write(indent_str+'<{} size="{}"'.format(self.tag,self.size))
        if self.flags is not None:
            f.write(' flags="{}"'.format(self.flags))
        f.write('>\n')
        for child in self.children:
            child.write(f,indent+1)
        f.write(indent_str+'</{}>\n'.format(self.tag))

    def fmt(self):
        tag = self.tag
        p = self.parent
        while True:
            fmt = fmt_rec.get(tag)
            if fmt is not None:
                if fmt[0]=="size":
                    fmt = fmt[1].get(str(self.size))
                    if fmt is None: break
                    return fmt
                else:
                    return fmt
            if p is None: break
            tag = p.tag + '.' + tag
            p = p.parent
        if self.flags is None:
            return [('s',None)]
        else:
            return ["children"]

class attr:
    def __init__(self,fmt,val):
        self.fmt = fmt
        self.val = val
    order = ['fmt','name','note']
    def write(self,f,indent=0):
        indent_str = ' '*indent
        f.write(indent_str+'<x')
        nfmt = len(self.fmt)
        for i in range(len(attr.order)):
            if i>=nfmt: break
            x = self.fmt[i]
            if x is None: continue
            f.write(' {}="{}"'.format(attr.order[i],x))
        f.write('>')
        if len(self.val)==1:
            f.write(xml_safe(self.val[0]))
        else:
            f.write('\n')
            for x in self.val:
                f.write(indent_str+' <v>'+xml_safe(x)+'</v>\n')
            f.write(indent_str)
        f.write('</x>\n')

rec_struct = struct.Struct('4sI')
flags_struct = struct.Struct('8s')

def read(data,a,b,parent=None):
    recs = [ ]
    while True:
        try:
            rec = record(*rec_struct.unpack_from(data,a),parent)
        except:
            print('Error at file pos:',a)
            raise
        a += 8
        if (parent is None) or (rec.tag in fmt_flg):
            rec.flags = rb2str(flags_struct.unpack_from(data,a)[0])
            a += 8
        fmts = rec.fmt()

        end = a + rec.size
        if flags['v']:
            print('{:4} {:8} {:8} {:8} {:8}'.format(rec.tag,rec.size,a,end,b))

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

if len(sys.argv)==3:
    ofname = sys.argv[2]
else:
    ofname = re.sub(r'^.*[/\\]','',
             re.sub(r'\.[^.]+$','',sys.argv[1])+'.xml')
print('writing',ofname)
with open(ofname,'w') as f:
    f.write('<file name="'+sys.argv[1]+'">\n')
    for node in tree:
        node.write(f)
    f.write('</file>\n')

