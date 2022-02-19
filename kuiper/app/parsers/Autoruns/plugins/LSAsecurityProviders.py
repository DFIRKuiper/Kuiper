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


class LSAsecurityProviders():
    def __init__(self,prim_hive,log_files):
        self.prim_hive = prim_hive
        self.log_files = log_files

    def run(self):
        lst = []
        "use the SYSTEM hive to get the result"
        Registry_Path_G1 = [u'ControlSet001\\Control\\SecurityProviders',
                            u'ControlSet001\\Control\\Lsa\\OSConfig']
        SK_Name_G1 =['SecurityProviders', 'Security Packages']
        Registry_Path_G2 = 'ControlSet001\\Control\\Lsa'
        hive = get_hive(self.prim_hive,self.log_files)
        ##########
        ###Group 1
        ##########
        for key_path, SKN in zip(Registry_Path_G1,SK_Name_G1):
            key = hive.find_key(key_path)
            if key:
                for x in key.values():
                    if x.name() == SKN:
                        TS = key.last_written_timestamp().isoformat()
                        Path = x.data()
                        record = OrderedDict([
                            ("@timestamp",TS),
                            ("Launch String", key_path),
                            ("Category", "LSA Providers"),
                            ("Name", x.name()),
                            ("Path", Path)
                            ])
                        lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
            else:
                logging.info(u"[{}] {} not found.".format('LSA Providers', key))

        ##########
        ###Group 2
        ##########
        key = hive.find_key(Registry_Path_G2)
        if key:
            for x in key.values():
                if x.name() == 'Authentication Packages' or x.name() == 'Notification Packages' or x.name() == 'Security Packages':
                    TS = key.last_written_timestamp().isoformat()
                    for d in x.data():
                        Path = strip_control_characters(d)
                        record = OrderedDict([
                            ("@timestamp",TS),
                            ("Launch String", Registry_Path_G2),
                            ("Category", "PrintMonitorDLLs"),
                            ("Name", x.name()),
                            ("Path", Path)
                        ])
                        lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
        else:
            logging.info(u"[{}] {} not found.".format('LSA Providers', key))
                    
        return lst
