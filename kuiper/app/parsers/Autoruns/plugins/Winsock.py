import json
import logging
import traceback
from collections import OrderedDict
from lib.helper import convert_datetime
from lib.helper import ComplexEncoder
from lib.helper import strip_control_characters
from lib.hive_yarp import get_hive
from lib.helper import strip_control_characters
from yarp import *
import re

class Winsock():
    def __init__(self,prim_hive,log_files):
        self.prim_hive = prim_hive
        self.log_files = log_files

    def run(self):
        lst = []
        "use the SYSTEM hive to get the result"
        Registry_Path_G1 = [u'ControlSet001\\Services\\WinSock2\\Parameters\\Protocol_Catalog9\\Catalog_Entries',
                            u'ControlSet001\\Services\\WinSock2\\Parameters\\Protocol_Catalog9\\Catalog_Entries64',
                            u'ControlSet001\\Services\\WinSock2\\Parameters\\NameSpace_Catalog5\\Catalog_Entries',
                            u'ControlSet001\\Services\\WinSock2\\Parameters\\NameSpace_Catalog5\\Catalog_Entries64']
        Registry_Path_G2 = u'ControlSet001\\Control\\NetworkProvider\\Order'
        hive = get_hive(self.prim_hive,self.log_files)
        for key_path in Registry_Path_G1:
            key = hive.find_key(key_path)
            if key:
                for SK in key.subkeys():
                    for x in SK.values():
                        if x.name() == 'PackedCatalogItem':
                            TS = SK.last_written_timestamp().isoformat()
                            Bin = x.data()
                            Str = Bin.decode('ascii','ignore')
                            Path = strip_control_characters(Str)
                            record = OrderedDict([
                                ("@timestamp",TS),
                                ("Launch String", key_path),
                                ("Category", "Winsock"),
                                ("Path", Path)
                            ])
                            lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
                        if x.name() == 'LibraryPath':
                            TS = SK.last_written_timestamp().isoformat()
                            Path = strip_control_characters(x.data())
                            record = OrderedDict([
                                ("@timestamp",TS),
                                ("Launch String", key_path),
                                ("Category", "Winsock"),
                                ("Path", Path)
                            ])
                            lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
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
                                    TS = key.last_written_timestamp().isoformat()
                                    Path = strip_control_characters(y.data())
                                    record = OrderedDict([
                                        ("@timestamp",TS),
                                        ("Launch String", key_path),
                                        ("Category", "Winsock"),
                                        ("name", i),
                                        ("Path", Path)
                                    ])
                                    lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))

                        else:
                            logging.info(u"[{}] {} not found.".format('Winsock', key))
                else:
                    logging.info(u"[{}] {} not found.".format('Winsock', key))
                    
        return lst
