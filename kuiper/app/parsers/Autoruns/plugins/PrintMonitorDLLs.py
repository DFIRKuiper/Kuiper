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

class PrintMonitorDLLs():
    def __init__(self,prim_hive,log_files):
        self.prim_hive = prim_hive
        self.log_files = log_files

    def run(self):
        lst = []
        "use the SYSTEM && SOFTWARE hive to get the result"
        Registry_Path_G1 = [u'ControlSet001\\Control\\Print\\Monitors',
                            u'ControlSet001\\Control\\Print\\Providers']
        SK_Name_G1 = ['Driver', 'Name']
        Registry_Path_G2 = 'Microsoft\Windows NT\CurrentVersion\Ports'
        hive = get_hive(self.prim_hive,self.log_files)
        ##########
        ###Group 1
        ##########
        for key_path, SKN in zip(Registry_Path_G1, SK_Name_G1):
            key = hive.find_key(key_path)
            if key:
                for SK in key.subkeys():
                    for x in SK.values():
                        if x.name() == SKN:
                            TS = SK.last_written_timestamp().isoformat()
                            Path = strip_control_characters(x.data())
                            record = OrderedDict([
                                ("@timestamp",TS),
                                ("Launch String", key_path),
                                ("Category", "PrintMonitorDLLs"),
                                ("Name", x.name()),
                                ("Path", Path)
                            ])
                            lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
            else:
                logging.info(u"[{}] {} not found.".format('PrintMonitorDLLs', key))

        ##########
        ###Group 2
        ##########
        key = hive.find_key(Registry_Path_G2)
        if key:
            for x in key.values():
                if not(re.search('(COM|LPT|PORTPROMPT|FILE|nul|Ne)(\d{1,2})',x.name())):
                    TS = key.last_written_timestamp().isoformat()
                    Path = strip_control_characters(x.data())
                    record = OrderedDict([
                        ("@timestamp",TS),
                        ("Launch String", Registry_Path_G2),
                        ("Category", "PrintMonitorDLLs"),
                        ("Name", x.name()),
                        ("Path", Path)
                    ])
                    lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
        else:
            logging.info(u"[{}] {} not found.".format('PrintMonitorDLLs', key))
                    
        return lst
