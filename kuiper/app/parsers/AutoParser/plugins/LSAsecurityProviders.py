import json
import logging
from lib.helper import ComplexEncoder
from lib.helper import strip_control_characters
from yarp import *

Entry = {"@timestamp": "N/A", "Launch String": "N/A", "Category": "LSA Security Providers", "Path": "N/A", "Name": "N/A"}
class LSAsecurityProviders():
    def __init__(self,prim_hive):
        self.prim_hive = prim_hive

    def run(self):
        lst_json = []
        lst_csv = []
        "use the SYSTEM hive to get the result"
        Registry_Path_G1 = [u'ControlSet001\\Control\\SecurityProviders',
                            u'ControlSet001\\Control\\Lsa\\OSConfig']
        SK_Name_G1 =['SecurityProviders', 'Security Packages']
        Registry_Path_G2 = 'ControlSet001\\Control\\Lsa'
        hive = Registry.RegistryHive(open(self.prim_hive, 'rb'))
        ##########
        ###Group 1
        ##########
        for key_path, SKN in zip(Registry_Path_G1,SK_Name_G1):
            key = hive.find_key(key_path)
            if key:
                for x in key.values():
                    if x.name() == SKN:
                        Entry["@timestamp"] = key.last_written_timestamp().isoformat()
                        Entry["Name"] = x.name()
                        Entry["Path"] = x.data()
                        Entry["Launch String"] = key_path
                        lst_json.append(u"{}".format(json.dumps(Entry.copy(), cls=ComplexEncoder)))
                        lst_csv.append(Entry.copy()) 
            else:
                logging.info(u"[{}] {} not found.".format('LSA Providers', key))

        ##########
        ###Group 2
        ##########
        key = hive.find_key(Registry_Path_G2)
        if key:
            for x in key.values():
                if x.name() == 'Authentication Packages' or x.name() == 'Notification Packages' or x.name() == 'Security Packages':
                    for d in x.data():
                        Entry["@timestamp"] = key.last_written_timestamp().isoformat()
                        Entry["Name"] = x.name()
                        Entry["Path"] = strip_control_characters(d)
                        Entry["Launch String"] = Registry_Path_G2
                        lst_json.append(u"{}".format(json.dumps(Entry.copy(), cls=ComplexEncoder)))
                        lst_csv.append(Entry.copy())
        else:
            logging.info(u"[{}] {} not found.".format('LSA Providers', key))
                    
        return lst_json, lst_csv, Entry.keys()