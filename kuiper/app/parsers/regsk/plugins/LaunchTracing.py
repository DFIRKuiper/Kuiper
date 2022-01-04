import json
import logging
import traceback
from collections import OrderedDict
from lib.helper import convert_datetime
from lib.helper import ComplexEncoder
from lib.hive_yarp import get_hive
from yarp import *


class LaunchTracing():

    def __init__(self,prim_hive,log_files):
        self.prim_hive = prim_hive
        self.log_files = log_files

    def run(self):
        lst = []
        "use the SOFTWARE hive to get the result"
        LaunchTracing_user_settings_path = u"\\Wow6432Node\\Microsoft\\Tracing"
        hive = get_hive(self.prim_hive,self.log_files)
        LaunchTracing_user_settings_key = hive.find_key(LaunchTracing_user_settings_path)
        if LaunchTracing_user_settings_key:
            for sid_key in LaunchTracing_user_settings_key.subkeys():
                sid_name = sid_key.name()
                timestamp = sid_key.last_written_timestamp().isoformat()
                record = OrderedDict([
                        ("name", sid_name),
                        ("Excution_Time", timestamp),
                        ("@timestamp", timestamp)

                    ])

                lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
        else:
            logging.info(u"[{}] {} not found.".format('LaunchTracing', LaunchTracing_user_settings_path))

        return lst
