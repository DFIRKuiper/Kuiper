#!/usr/bin/python

import os
import sys

from Registry import Registry

# from http://stackoverflow.com/a/9806045/87207
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
parentparentdir = os.path.dirname(parentdir)
sys.path.append(parentparentdir)
from ShellItems import SHITEMLIST
sys.path.pop()


def hex_dump(data):
    """
    see http://code.activestate.com/recipes/142812/
    """
    byte_format = {}
    for c in xrange(256):
        if c > 126:
            byte_format[c] = '.'
        elif len(repr(chr(c))) == 3 and chr(c):
            byte_format[c] = chr(c)
        else:
            byte_format[c] = '.'

    def format_bytes(s):
        return "".join([byte_format[ord(c)] for c in s])

    def dump(src, length=16):
        N = 0
        result = ''
        while src:
            s, src = src[:length], src[length:]
            hexa = ' '.join(["%02X" % ord(x) for x in s])
            s = format_bytes(s)
            result += "%04X   %-*s   %s\n" % (N, length * 3, hexa, s)
            N += length
        return result
    return dump(data)


def test(filename):
    r = Registry.Registry(filename)
    k = r.open("Local Settings\\Software\\Microsoft\\Windows\\Shell\\BagMRU\\1\\0\\0")
    v = k.value("0")

    print hex_dump(v.value())

    l = SHITEMLIST(v.value(), 0, False)
    for index, item in enumerate(l.items()):
        print "item:", index
        print "type:", item.__class__.__name__
        print "name:", item.name()

        # its a SHITEM_FILEENTRY
        print "short name:", item.short_name()
        print "off long name:", item._off_long_name
        print "off long name size:", item._off_long_name_size
        print "long name size:", hex(item.long_name_size())
        print "mtime:", item.m_date()


def main():
    import sys
    hive = sys.argv[1]

    import hashlib
    m = hashlib.md5()
    with open(hive, 'rb') as f:
        m.update(f.read())
    if m.hexdigest() != "a83c09811f508399e1a23f674897da69":
        print "Please use the UsrClass hive with MD5 a83c09811f508399e1a23f674897da69"
        sys.exit(-1)

    test(hive)


if __name__ == "__main__":
    main()
