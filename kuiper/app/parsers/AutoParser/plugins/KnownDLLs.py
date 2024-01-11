import logging
import json
from lib.helper import ComplexEncoder
from lib.helper import strip_control_characters
from yarp import *

Entry = {"@timestamp": "N/A", "Launch String": "N/A", "Category": "KnownDLLs", "Name": "N/A"}
class KnownDLLs():
    def __init__(self,prim_hive):
        self.prim_hive = prim_hive

    def run(self):
        lst_json = []
        lst_csv = []
        "use the SYSTEM hive to get the result"
        Registry_Path = u"ControlSet001\Control\Session Manager\KnownDLLs"
        hive = Registry.RegistryHive(open(self.prim_hive, 'rb'))
        Registry_Key = hive.find_key(Registry_Path)
        if Registry_Key:
            for x in Registry_Key.values():
                Entry["@timestamp"] = Registry_Key.last_written_timestamp().isoformat()
                Entry["Name"] = strip_control_characters(x.data())
                Entry["Launch String"] = Registry_Path
                lst_json.append(u"{}".format(json.dumps(Entry.copy(), cls=ComplexEncoder)))
                lst_csv.append(Entry.copy())  
        else:
            logging.info(u"[{}] {} not found.".format("KnownDLLs", Registry_Path))        

        return lst_json, lst_csv, Entry.keys()
