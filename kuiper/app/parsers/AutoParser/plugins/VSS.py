import json
import logging
from lib.helper import ComplexEncoder
from yarp import *

Entry = {"@timestamp": "N/A", "Path": "N/A", "Category": "Volume Shadow Service"}
lst_json = []
lst_csv = []
class VSS():
    def __init__(self,prim_hive):
        self.prim_hive = prim_hive
    def RecursiveKey(self, key):
	    self.GetKey(key)
	    for subkey in key.subkeys():
		    self.RecursiveKey(subkey)
    def GetKey(self, key):
        Entry["@timestamp"] = key.last_written_timestamp().isoformat()
        Entry["Path"] = key.path()
        lst_json.append(u"{}".format(json.dumps(Entry.copy(), cls=ComplexEncoder)))
        lst_csv.append(Entry.copy())

    def run(self):
        "use the SYSTEM hive to get the result"
        REG_Path_1 = [u'ControlSet002\Enum\STORAGE\VolumeSnapshot',
                      u'ControlSet001\Enum\STORAGE\VolumeSnapshot']
        REG_Path_2 = [u'ControlSet001\Control\DeviceClasses',
                      u'ControlSet002\Control\DeviceClasses']
        hive = Registry.RegistryHive(open(self.prim_hive, 'rb'))
        for p in REG_Path_1:
            Key = hive.find_key(p)
            if Key:
                self.RecursiveKey(Key)     
            else:
                logging.info(u"[{}] {} not found.".format('VSS', Key))
        for p in REG_Path_2:
            Key = hive.find_key(p)
            if Key:
                for subkey in Key.subkeys():
                    for SK in subkey.subkeys():
                        if 'VolumeSnapshot' in SK.name():
                            self.GetKey(SK)
            else:
                logging.info(u"[{}] {} not found.".format('VSS', Key))
        return lst_json, lst_csv, Entry.keys()