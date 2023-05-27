import json
import logging
from lib.helper import ComplexEncoder
from lib.helper import strip_control_characters
from yarp import *

Entry = {"@timestamp": "N/A", "Launch String": "N/A", "Category": "Codecs", "Path": "N/A", "Name": "N/A"}
class Codecs():
    def __init__(self,prim_hive):
        self.prim_hive = prim_hive
        
    def run(self):
        CLSID = []
        Launch_String = []
        lst_json = []
        lst_csv = []
        "use the SOFTWARE && Ntuser hive to get the result"
        hive = Registry.RegistryHive(open(self.prim_hive, 'rb'))
        REG_Path_G1 = [ 'Wow6432Node\Microsoft\Windows NT\CurrentVersion\Drivers32',
                        'Microsoft\Windows NT\CurrentVersion\Drivers32'
                        u'\\Software\\Wow6432Node\\Microsoft\\Windows NT\\CurrentVersion\\Drivers32',
                        u'\\Software\\Microsoft\\Windows NT\\CurrentVersion\\Drivers32']
        
        REG_Path_G2 = [ 'Wow6432Node\Classes\Filter',
                        'Classes\Filter',
                        'Wow6432Node\Classes\CLSID\{083863F1-70DE-11d0-BD40-00A0C911CE86}\Instance',
                        'Wow6432Node\Classes\CLSID\{AC757296-3522-4E11-9862-C17BE5A1767E}\Instance',
                        'Wow6432Node\Classes\CLSID\{7ED96837-96F0-4812-B211-F13C24117ED3}\Instance',
                        'Wow6432Node\Classes\CLSID\{ABE3B9A4-257D-4B97-BD1A-294AF496222E}\Instance',
                        'Classes\CLSID\{083863F1-70DE-11d0-BD40-00A0C911CE86}\Instance',
                        'Classes\CLSID\{AC757296-3522-4E11-9862-C17BE5A1767E}\Instance',
                        'Classes\CLSID\{7ED96837-96F0-4812-B211-F13C24117ED3}\Instance',
                        'Classes\CLSID\{ABE3B9A4-257D-4B97-BD1A-294AF496222E}\Instance',
                        u'\\Software\\Wow6432Node\\Classes\\CLSID\\{083863F1-70DE-11d0-BD40-00A0C911CE86}\\Instance',
                        u'\\Software\\Wow6432Node\\Classes\\CLSID\\{AC757296-3522-4E11-9862-C17BE5A1767E}\\Instance',
                        u'\\Software\\Wow6432Node\\Classes\\CLSID\\{7ED96837-96F0-4812-B211-F13C24117ED3}\\Instance',
                        u'\\Software\\Wow6432Node\\Classes\\CLSID\\{ABE3B9A4-257D-4B97-BD1A-294AF496222E}\\Instance',
                        u'\\Software\\Classes\\CLSID\\{083863F1-70DE-11d0-BD40-00A0C911CE86}\\Instance',
                        u'\\Software\\Classes\\CLSID\\{AC757296-3522-4E11-9862-C17BE5A1767E}\\Instance',
                        u'\\Software\\Classes\\CLSID\\{7ED96837-96F0-4812-B211-F13C24117ED3}\\Instance',
                        u'\\Software\\Classes\\CLSID\\{ABE3B9A4-257D-4B97-BD1A-294AF496222E}\\Instance'
                        ]

        ##########
        ###Group 1
        ##########
        for p in REG_Path_G1:
            Key = hive.find_key(p)
            if Key:
                for x in Key.values():
                    Entry["@timestamp"] = Key.last_written_timestamp().isoformat()
                    Entry["Path"] = strip_control_characters(x.data())
                    Entry["Launch String"] = p
                    Entry["Name"] = x.name()
                    lst_json.append(u"{}".format(json.dumps(Entry.copy(), cls=ComplexEncoder)))
                    lst_csv.append(Entry.copy())  
            else:
                logging.info(u"[{}] {} not found.".format('Codecs', p))
        ##########
        ###Group 2
        ##########
        for p in REG_Path_G2:
            Key = hive.find_key(p)
            if Key:
                for SK in Key.subkeys():
                    CLSID.append(SK.name())
                    Launch_String.append(p)
            else:
                logging.info(u"[{}] {} not found.".format('Codecs', p))
        ###############
        ###GET BIN Path
        ###############       
        for ID, LS in zip(CLSID, Launch_String):
            CLSID_path = ["Wow6432Node\Classes\CLSID\\" + ID + "\InprocServer32", "Classes\CLSID\\" + ID + "\InprocServer32"]
            for p in CLSID_path:
                Bin_key = hive.find_key(p)
                if Bin_key:
                    for y in Bin_key.values():
                        if y.name() == "":
                            Entry["@timestamp"] = Bin_key.last_written_timestamp().isoformat()
                            Entry["Path"] = strip_control_characters(y.data())
                            Entry["Launch String"] = LS
                            Entry["Name"] = "N/A"
                            lst_json.append(u"{}".format(json.dumps(Entry.copy(), cls=ComplexEncoder)))
                            lst_csv.append(Entry.copy())  
                else:
                    logging.info(u"[{}] {} not found.".format('Codecs', Bin_key))

        return lst_json, lst_csv, Entry.keys()
