
shellbags.py
===============

Introduction
------------
shellbags.py is a cross-platform, open-source shellbag parser.
The webpage
http://www.williballenthin.com/forensics/shellbags/index.html
describes the algorithm in detail.
Note that shellbags.py was originally developed as a sample
for python-registry, so this repository is a fork that contains
the python-registry history through version v0.2.4.1.
The initial shellbags.py tag v0.5.

Dependencies
------------
shellbags.py requires Python2.7, argparse, six and python-registry.

Usage
-----
shellbags.py accepts the path to a raw Windows Registry hive.
This hive should be acquired forensically.
To ensure interoperability, output is formatted according to the Bodyfile specification by default.

Parameters:
usage: shellbags.py [-h] [-v] [-p] [-o {csv,bodyfile}] file [file ...]

Parse Shellbag entries from a Windows Registry.

positional arguments:
  file        Windows Registry hive file(s)

optional arguments:
  -h, --help  show this help message and exit
  -v          Print debugging information while parsing
  -p          If debugging messages are enabled, augment the formatting with
              ANSI color codes
  -o {csv,bodyfile}  Output format: csv or bodyfile; default is bodyfile

Example: 
$ python shellbags.py ~/projects/registry-files/willi/xp/NTUSER.DAT.copy0
0|\My Documents (Shellbag)|0|0|0|0|0|978325200|978325200|18000|978325200
0|\My Documents\Downloads (Shellbag)|0|0|0|0|0|1282762334|1282762334|18000|1281987456
0|\My Documents\My Dropbox (Shellbag)|0|0|0|0|0|1281989096|1282762296|18000|1281989050
0|\My Documents\My Music (Shellbag)|0|0|0|0|0|1281995426|1282239780|18000|1281987154
0|\My Documents\My Pictures (Shellbag)|0|0|0|0|0|1281995426|1282239780|18000|1281987152
0|\My Documents\My Dropbox (Shellbag)|0|0|0|0|0|978325200|978325200|18000|978325200
0|\My Documents\My Dropbox\Tools (Shellbag)|0|0|0|0|0|1281989092|1281989092|18000|1281989088
0|\My Documents\My Dropbox\Tools\Windows (Shellbag)|0|0|0|0|0|1281989140|1281989140|18000|1281989092
0|\My Documents\My Dropbox\Tools\Windows\7zip (Shellbag)|0|0|0|0|0|1281993604|1284668784|18000|1281989140
0|\My Documents\My Dropbox\Tools\Windows\Adobe (Shellbag)|0|0|0|0|0|1281994956|1284668784|18000|1281989140
0|\My Documents\My Dropbox\Tools\Windows\Bitpim (Shellbag)|0|0|0|0|0|1281994656|1284668784|18000|1281989140

Wanted
------
*) Bug reports.
*) Feedback.

License
-------
shellbags.py is released under the Apache 2.0 license.

Sources
-------
1) "Using shellbag information to reconstruct user activities" by 
   Yuandong Zhu, Pavel Gladyshev, and Joshua James which may be
   accessed http://www.dfrws.org/2009/proceedings/p69-zhu.pdf
2) "MiTeC Registry Analyzer" by Allan S Hay, which may be accessed at
   http://mysite.verizon.net/hartsec/files/WRA_Guidance.pdf
3) "sbag" by TZWorks, which may be accessed at 
   http://www.tzworks.net/prototype_page.php?proto_id=14
4) "Shell BAG Format Analysis" by Yogesh Khatri, which may be accessed
   at https://42llc.net/?p=385
5) "Windows Shell Item format specification" by Joachim Metz, which
   may be accessed at http://download.polytechnic.edu.na/pub4/download.sourceforge.net/pub/sourceforge/l/project/li/liblnk/Documentation/Windows%20Shell%20Item%20format/Windows%20Shell%20Item%20format.pdf
   
