import json
import logging
from lib.helper import ComplexEncoder
from lib.helper import strip_control_characters
from yarp import *

Entry = {"@timestamp": "N/A", "Launch String": "N/A", "Category": "AppinitDLLs", "Name": "N/A"}

class AppinitDLLs():
    def __init__(self,prim_hive):
        self.prim_hive = prim_hive

    def run(self):
        lst_json = []
        lst_csv = []
        "use the SOFTWARE && SYSTEM hive to get the result"
        REG_Path_G1 = ['Microsoft\Windows NT\CurrentVersion\Windows',
                       'Wow6432Node\Microsoft\Windows NT\CurrentVersion\Windows']
        REG_Path_G2 = u'ControlSet001\\Control\\Session Manager\\AppCertDlls'
        hive = Registry.RegistryHive(open(self.prim_hive, 'rb'))
        for p in REG_Path_G1:
            Registry_Key = hive.find_key(p)
            if Registry_Key:
                for x in Registry_Key.values():
                    if x.name() == 'AppinitDLLs':
                        Entry["@timestamp"] = Registry_Key.last_written_timestamp().isoformat()
                        Entry["Name"] = strip_control_characters(x.data())
                        Entry["Launch String"] = p                        
                        lst_json.append(u"{}".format(json.dumps(Entry.copy(), cls=ComplexEncoder)))
                        lst_csv.append(Entry.copy()) 
            else:
                logging.info(u"[{}] {} not found.".format('AppinitDLLs', p))
        Registry_Key = hive.find_key(REG_Path_G2)
        if Registry_Key:
            for x in Registry_Key.values():
                Entry["@timestamp"] = Registry_Key.last_written_timestamp().isoformat()
                Entry["Name"] = strip_control_characters(x.data())
                Entry["Launch String"] = REG_Path_G2                        
                lst_json.append(u"{}".format(json.dumps(Entry.copy(), cls=ComplexEncoder)))
                lst_csv.append(Entry.copy()) 
        else:
            logging.info(u"[{}] {} not found.".format('AppinitDLLs', REG_Path_G2))

        return lst_json, lst_csv, Entry.keys()
