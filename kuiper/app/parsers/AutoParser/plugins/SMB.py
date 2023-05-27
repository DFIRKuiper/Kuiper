import logging
import json
from lib.helper import ComplexEncoder
from lib.helper import strip_control_characters
from yarp import *

Entry = {"@timestamp": "N/A", "Launch String": "N/A", "Category": "SMB", "User Name": "N/A", "Dst IP": "N/A"}
class SMB():
    def __init__(self,prim_hive):
        self.prim_hive = prim_hive

    def run(self):
        lst_json = []
        lst_csv = []
        "use the Ntuser hive to get the result"
        REGPath = u"Software\Microsoft\Windows\CurrentVersion\Explorer\MountPoints2"
        hive = Registry.RegistryHive(open(self.prim_hive, 'rb'))
        Registry_Key = hive.find_key(REGPath)
        if Registry_Key:
            for SK in Registry_Key.subkeys():
                if SK.name().startswith('#'):
                    Entry["@timestamp"] = SK.last_written_timestamp().isoformat()
                    String = SK.name().replace('##', '')
                    Entry["Dst IP"] = String[:String.find('#')]
                    Entry["Dst Folder"] = String[String.find('#')+1:]
                    lst_json.append(u"{}".format(json.dumps(Entry.copy(), cls=ComplexEncoder)))
                    lst_csv.append(Entry.copy())  
        else:
            logging.info(u"[{}] {} not found.".format("SMB", REGPath))        

        return lst_json, lst_csv, Entry.keys()
        