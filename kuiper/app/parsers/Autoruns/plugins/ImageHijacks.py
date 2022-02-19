import json
import logging
import traceback
from collections import OrderedDict
from lib.helper import convert_datetime
from lib.helper import ComplexEncoder
from lib.helper import strip_control_characters
from lib.hive_yarp import get_hive
from lib.helper import strip_control_characters
from yarp import *


class ImageHijacks():
    def __init__(self,prim_hive,log_files):
        self.prim_hive = prim_hive
        self.log_files = log_files

    def run(self):
        lst = []
        hive = get_hive(self.prim_hive,self.log_files)
        "use the SOFTWARE && Ntuser hive to get the result"
        REG_Path_G1 = ['Microsoft\Windows NT\CurrentVersion\Image File Execution Options',
                       'Wow6432Node\Microsoft\Windows NT\CurrentVersion\Image File Execution Options',
                       'Microsoft\Windows NT\CurrentVersion\SilentProcessExit',
                       'Wow6432Node\Microsoft\Windows NT\CurrentVersion\SilentProcessExit']
        REG_Path_G2 = ['Microsoft\Microsoft\Command Processor',
                       'Wow6432Node\Microsoft\Command Processor',
                       'Classes\Exefile\Shell\Open\Command',
                       'Classes\htmlfile\shell\open\command',
                       u'\\Software\\Microsoft\\Command Processor',
                       u'\\Software\\Classes\\Exefile\\Shell\\Open\\Command',
                       u'\\Software\\Classes\\htmlfile\\shell\\open\\command']
        SK_Name_G2 = [ 'Autorun', 'Autorun', '', '', 'Autorun', '', '']
        REG_Path_G3 = ['Classes\.exe',
                       'Classes\.cmd',
                       u'\\Software\\Classes\\.exe',
                       u'\\Software\\Classes\\.cmd']
        
        for p in REG_Path_G1:
            Key = hive.find_key(p)
            if Key:
                for SK in Key.subkeys():
                    for x in SK.values():
                        if x.name() == 'Debugger' or x.name() == 'MonitorProcess':
                            TS = SK.last_written_timestamp().isoformat()
                            Path = strip_control_characters(x.data())
                            record = OrderedDict([
                                ("@timestamp",TS),
                                ("Launch String", p),
                                ("Category", "ImageHijacks"),
                                ("Binary Name", SK.name()),
                                ("Path", Path)])
                            lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder))) 
            else:
                logging.info(u"[{}] {} not found.".format('ImageHijacks', p))
        # Group 2
        
        for p, SKN in zip(REG_Path_G2, SK_Name_G2):
            Key = hive.find_key(p)
            if Key:
                for x in Key.values():
                    if x.name() == SKN:
                        Data = x.data()
                        TS = Key.last_written_timestamp().isoformat()
                        record = OrderedDict([
                            ("@timestamp",TS),
                            ("Launch String", p),
                            ("Category", "ImageHijacks"),
                            ("Data", Data)])
                        lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder))) 
            else:
                logging.info(u"[{}] {} not found.".format('ImageHijacks', p))

        for p in REG_Path_G3:
            Key = hive.find_key(p)
            if Key:
                for x in Key.values():
                    if x.name() == '':
                        Value = strip_control_characters(x.data())
                        Path = "Classes\\" + Value + "\shell\open\command"
                        K = hive.find_key(Path)
                        if K:
                            for x in Key.values():
                                if x.name() == '':
                                    TS = K.last_written_timestamp().isoformat()
                                    Data = x.data()
                                    record = OrderedDict([
                                        ("@timestamp",TS),
                                        ("Launch String", p),
                                        ("Category", "ImageHijacks"),
                                        ("Name", Data)])
                        lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
            else:
                logging.info(u"[{}] {} not found.".format('ImageHijacks', p))

        return lst
