import json
import logging
import re
from lib.helper import ComplexEncoder
from lib.helper import strip_control_characters
from yarp import *

Entry = {"@timestamp": "N/A", "Launch String": "N/A", "Category": "Print Monitor DLLs", "Path": "N/A", "Name": "N/A"}
class PrintMonitorDLLs():
    def __init__(self,prim_hive):
        self.prim_hive = prim_hive

    def run(self):
        lst_json = []
        lst_csv = []
        "use the SYSTEM && SOFTWARE hive to get the result"
        Registry_Path_G1 = [u'ControlSet001\\Control\\Print\\Monitors',
                            u'ControlSet001\\Control\\Print\\Providers']
        SK_Name_G1 = ['Driver', 'Name']
        Registry_Path_G2 = 'Microsoft\Windows NT\CurrentVersion\Ports'
        hive = Registry.RegistryHive(open(self.prim_hive, 'rb'))
        ##########
        ###Group 1
        ##########
        for key_path, SKN in zip(Registry_Path_G1, SK_Name_G1):
            key = hive.find_key(key_path)
            if key:
                for SK in key.subkeys():
                    for x in SK.values():
                        if x.name() == SKN:
                            Entry["@timestamp"] = SK.last_written_timestamp().isoformat()
                            Entry["Name"] = x.name()
                            Entry["Path"] = strip_control_characters(x.data())
                            Entry["Launch String"] = key_path
                            lst_json.append(u"{}".format(json.dumps(Entry.copy(), cls=ComplexEncoder)))
                            lst_csv.append(Entry.copy())
            else:
                logging.info(u"[{}] {} not found.".format('Print Monitor DLLs', key))

        ##########
        ###Group 2
        ##########
        key = hive.find_key(Registry_Path_G2)
        if key:
            for x in key.values():
                if not(re.search('(COM|LPT|PORTPROMPT|FILE|nul|Ne)(\d{1,2})',x.name())):
                    Entry["@timestamp"] = key.last_written_timestamp().isoformat()
                    Entry["Name"] = x.name()
                    Entry["Path"] = strip_control_characters(x.data())
                    Entry["Launch String"] = Registry_Path_G2
                    lst_json.append(u"{}".format(json.dumps(Entry.copy(), cls=ComplexEncoder)))
                    lst_csv.append(Entry.copy())
        else:
            logging.info(u"[{}] {} not found.".format('Print Monitor DLLs', key))
                    
        return lst_json, lst_csv, Entry.keys()