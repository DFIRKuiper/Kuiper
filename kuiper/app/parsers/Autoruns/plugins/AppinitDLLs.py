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


class AppinitDLLs():
    def __init__(self,prim_hive,log_files):
        self.prim_hive = prim_hive
        self.log_files = log_files

    def run(self):
        lst = []
        "use the SOFTWARE && SYSTEM hive to get the result"
        REG_Path_G1 = ['Microsoft\Windows NT\CurrentVersion\Windows',
                       'Wow6432Node\Microsoft\Windows NT\CurrentVersion\Windows']
        REG_Path_G2 = u'ControlSet001\\Control\\Session Manager\\AppCertDlls'
        hive = get_hive(self.prim_hive,self.log_files)
        for p in REG_Path_G1:
            Registry_Key = hive.find_key(p)
            if Registry_Key:
                for x in Registry_Key.values():
                    if x.name() == 'AppinitDLLs':
                        Path = strip_control_characters(x.data())
                        TS = Registry_Key.last_written_timestamp().isoformat()
                        record = OrderedDict([
                            ("@timestamp",TS),
                            ("Launch String", "Microsoft\Windows NT\CurrentVersion\Windows"),
                            ("Category", 'AppinitDLLs'),
                            ("Name", Path)
                        ])
                        lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
            else:
                logging.info(u"[{}] {} not found.".format('AppinitDLLs', p))
        Registry_Key = hive.find_key(REG_Path_G2)
        if Registry_Key:
            for x in Registry_Key.values():
                Path = strip_control_characters(x.data())
                TS = Registry_Key.last_written_timestamp().isoformat()
                record = OrderedDict([
                    ("@timestamp",TS),
                    ("Launch String", "Microsoft\Windows NT\CurrentVersion\Windows"),
                    ("Category", 'AppinitDLLs'),
                    ("Name", Path)
                ])
                lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
        else:
            logging.info(u"[{}] {} not found.".format('AppinitDLLs', REG_Path_G2))

        return lst
