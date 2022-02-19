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


class BootExecute():
    def __init__(self,prim_hive,log_files):
        self.prim_hive = prim_hive
        self.log_files = log_files

    def run(self):
        lst = []
        "use the SYSTEM hive to get the result"
        Registry_Path = u'ControlSet001\Control\Session Manager'
        hive = get_hive(self.prim_hive,self.log_files)
        Registry_Key = hive.find_key(Registry_Path)
        if Registry_Key:
            for x in Registry_Key.values():
                if x.name() == 'BootExecute':
                    Data = x.data()
                    TS = Registry_Key.last_written_timestamp().isoformat()
                    record = OrderedDict([
                        ("@timestamp",TS),
                        ("Launch String", "ControlSet001\Control\Session Manager"),
                        ("Category", "BootExecute"),
                        ("Name", Data),
                    ])
                    lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
        else:
            logging.info(u"[{}] {} not found.".format('BootExecute', Registry_Path))

        return lst
