import json
import logging
from lib.helper import ComplexEncoder
from lib.helper import strip_control_characters
from yarp import *

Entry = {"@timestamp": "N/A", "Launch String": "N/A", "Category": "Image Hijacks", "Path": "N/A", "Name": "N/A"}
class ImageHijacks():
    def __init__(self,prim_hive):
        self.prim_hive = prim_hive

    def run(self):
        lst_json = []
        lst_csv = []
        hive = Registry.RegistryHive(open(self.prim_hive, 'rb'))
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
                            Entry["@timestamp"] = SK.last_written_timestamp().isoformat()
                            Entry["Path"] = strip_control_characters(x.data())
                            Entry["Launch String"] = p
                            Entry["Name"] = SK.name()
                            lst_json.append(u"{}".format(json.dumps(Entry.copy(), cls=ComplexEncoder)))
                            lst_csv.append(Entry.copy())
            else:
                logging.info(u"[{}] {} not found.".format('Image Hijacks', p))
        # Group 2
        
        for p, SKN in zip(REG_Path_G2, SK_Name_G2):
            Key = hive.find_key(p)
            if Key:
                for x in Key.values():
                    if x.name() == SKN:
                        Entry["@timestamp"] = Key.last_written_timestamp().isoformat()
                        Entry["Path"] = "N/A"
                        Entry["Launch String"] = p
                        Entry["Name"] = x.data()
                        lst_json.append(u"{}".format(json.dumps(Entry.copy(), cls=ComplexEncoder)))
                        lst_csv.append(Entry.copy())
            else:
                logging.info(u"[{}] {} not found.".format('Image Hijacks', p))

        for p in REG_Path_G3:
            Key = hive.find_key(p)
            if Key:
                for x in Key.values():
                    if x.name() == '':
                        Value = strip_control_characters(x.data())
                        Path = "Classes\\" + Value + "\shell\open\command"
                        K = hive.find_key(Path)
                        if K:
                            for x in K.values():
                                if x.name() == '':
                                    Entry["@timestamp"] = K.last_written_timestamp().isoformat()
                                    Entry["Path"] = "N/A"
                                    Entry["Launch String"] = p
                                    Entry["Name"] = x.data()
                                    lst_json.append(u"{}".format(json.dumps(Entry.copy(), cls=ComplexEncoder)))
                                    lst_csv.append(Entry.copy())
            else:
                logging.info(u"[{}] {} not found.".format('Image Hijacks', p))

        return lst_json, lst_csv, Entry.keys()
