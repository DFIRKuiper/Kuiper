import logging
import json
from lib.helper import ComplexEncoder
from lib.helper import strip_control_characters
from yarp import *

Entry = {"@timestamp": "N/A", "Launch String": "N/A", "Category": "RDP", "UserName": "N/A", "Dst_IP": "N/A"}
class RDP():
    def __init__(self,prim_hive):
        self.prim_hive = prim_hive

    def run(self):
        lst_json = []
        lst_csv = []
        "use the Ntuser hive to get the result"
        REGPath = u"Software\Microsoft\Terminal Server Client\Servers"
        hive = Registry.RegistryHive(open(self.prim_hive, 'rb'))
        Registry_Key = hive.find_key(REGPath)
        if Registry_Key:
            for SK in Registry_Key.subkeys():
                for x in SK.values():
                    Entry["@timestamp"] = SK.last_written_timestamp().isoformat()
                    Entry["UserName"] = x.data()
                    Entry["Dst_IP"] = SK.name()
                    lst_json.append(u"{}".format(json.dumps(Entry.copy(), cls=ComplexEncoder)))
                    lst_csv.append(Entry.copy())  
        else:
            logging.info(u"[{}] {} not found.".format("RDP", REGPath))        

        return lst_json, lst_csv, Entry.keys()