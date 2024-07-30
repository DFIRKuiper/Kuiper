import json
import logging
from lib.helper import ComplexEncoder
from lib.helper import strip_control_characters
from yarp import *

Entry = {"@timestamp": "N/A", "Launch String": "N/A", "Category": "Winsock", "Path": "N/A", "Name": "N/A"}
class Winsock():
    def __init__(self,prim_hive):
        self.prim_hive = prim_hive

    def run(self):
        lst_json = []
        lst_csv = []
        "use the SYSTEM hive to get the result"
        Registry_Path_G1 = [u'ControlSet001\\Services\\WinSock2\\Parameters\\Protocol_Catalog9\\Catalog_Entries',
                            u'ControlSet001\\Services\\WinSock2\\Parameters\\Protocol_Catalog9\\Catalog_Entries64',
                            u'ControlSet001\\Services\\WinSock2\\Parameters\\NameSpace_Catalog5\\Catalog_Entries',
                            u'ControlSet001\\Services\\WinSock2\\Parameters\\NameSpace_Catalog5\\Catalog_Entries64']
        Registry_Path_G2 = u'ControlSet001\\Control\\NetworkProvider\\Order'
        hive = Registry.RegistryHive(open(self.prim_hive, 'rb'))
        for key_path in Registry_Path_G1:
            key = hive.find_key(key_path)
            if key:
                for SK in key.subkeys():
                    for x in SK.values():
                        if x.name() == 'PackedCatalogItem':
                            Bin = x.data()
                            Str = Bin.decode('ascii','ignore')
                            Entry["@timestamp"] = SK.last_written_timestamp().isoformat()
                            Entry["Name"] = "N/A"
                            Entry["Path"] = strip_control_characters(Str)
                            Entry["Launch String"] = key_path
                            lst_json.append(u"{}".format(json.dumps(Entry.copy(), cls=ComplexEncoder)))
                            lst_csv.append(Entry.copy())
                        if x.name() == 'LibraryPath':
                            Entry["@timestamp"] = SK.last_written_timestamp().isoformat()
                            Entry["Name"] = "N/A"
                            Entry["Path"] = strip_control_characters(x.data())
                            Entry["Launch String"] = key_path
                            lst_json.append(u"{}".format(json.dumps(Entry.copy(), cls=ComplexEncoder)))
                            lst_csv.append(Entry.copy())
            else:
                logging.info(u"[{}] {} not found.".format('Winsock', key))
        Key = hive.find_key(Registry_Path_G2)
        if Key:
            for x in Key.values():
                if x.name() == 'ProviderOrder':
                    values = strip_control_characters(x.data())
                    x = values.split(',')
                    for i in x:
                        path = 'ControlSet001\\Services\\' + i + '\\NetworkProvider'
                        key = hive.find_key(path)
                        if key:
                            for y in key.values():
                                if y.name() == "ProviderPath":
                                    Entry["@timestamp"] = key.last_written_timestamp().isoformat()
                                    Entry["Name"] = i
                                    Entry["Path"] = strip_control_characters(y.data())
                                    Entry["Launch String"] = key_path
                                    lst_json.append(u"{}".format(json.dumps(Entry.copy(), cls=ComplexEncoder)))
                                    lst_csv.append(Entry.copy())
                        else:
                            logging.info(u"[{}] {} not found.".format('Winsock', key))
                else:
                    logging.info(u"[{}] {} not found.".format('Winsock', key))
                    
        return lst_json, lst_csv, Entry.keys()
