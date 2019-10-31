#!/usr/bin/python

import os
import sys

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
    with open(filename) as f:
        t = f.read()

    print hex_dump(t)

    l = SHITEMLIST(t, 0, False)
    for index, item in enumerate(l.items()):
        print "item:", index
        print "type:", item.__class__.__name__
        print "name:", item.name()
        print "mtime:", item.m_date()


def main():
    import sys
    hive = sys.argv[1]

    import hashlib
    m = hashlib.md5()
    with open(hive, 'rb') as f:
        m.update(f.read())
    if m.hexdigest() != "14f997a39bb131ff2a03aa3c62dc32ea":
        print "Please use the binary file with MD5 14f997a39bb131ff2a03aa3c62dc32ea"
        sys.exit(-1)

    test(hive)


if __name__ == "__main__":
    main()
