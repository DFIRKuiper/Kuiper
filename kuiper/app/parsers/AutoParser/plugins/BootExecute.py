import json
import logging
from lib.helper import ComplexEncoder
from lib.helper import strip_control_characters
from yarp import *

Entry = {"@timestamp": "N/A", "Launch String": "N/A", "Category": "Boot Execute", "Name": "N/A"}

class BootExecute():
    def __init__(self,prim_hive):
        self.prim_hive = prim_hive

    def run(self):
        lst_json = []
        lst_csv = []
        "use the SYSTEM hive to get the result"
        Registry_Path = u'ControlSet001\Control\Session Manager'
        hive = Registry.RegistryHive(open(self.prim_hive, 'rb'))
        Registry_Key = hive.find_key(Registry_Path)
        if Registry_Key:
            for x in Registry_Key.values():
                if x.name() == 'BootExecute':
                    Entry["@timestamp"] = Registry_Key.last_written_timestamp().isoformat()
                    Value = x.data()
                    name = Value[0].rstrip('\x00')
                    Entry["Name"] = name
                    Entry["Launch String"] = Registry_Path
                    lst_json.append(u"{}".format(json.dumps(Entry.copy(), cls=ComplexEncoder)))
                    lst_csv.append(Entry.copy())
        else:
            logging.info(u"[{}] {} not found.".format('Boot Execute', Registry_Path))

        return lst_json, lst_csv, Entry.keys()
