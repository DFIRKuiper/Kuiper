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


class RunMRU():
    def __init__(self,prim_hive,log_files):
        self.prim_hive = prim_hive
        self.log_files = log_files

    def run(self):
        lst = []
        "use the NTUSER.dat hive to get the result"
        RunMRU_user_settings_path = u'Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\RunMRU'
        hive = get_hive(self.prim_hive,self.log_files)
        RunMRU_user_settings_key = hive.find_key(RunMRU_user_settings_path)
        if RunMRU_user_settings_key:
            sid_key_values = iter(RunMRU_user_settings_key.values())
            timestamp = RunMRU_user_settings_key.last_written_timestamp().isoformat()
            while True:
                try:
                    value = next(sid_key_values)
                except StopIteration:
                    break
                except Exception as error:
                    logging.error(u"Error getting next value: {}".format(error))
                    continue

                sid_name = value.name()
                file_name = strip_control_characters(value.data())

                record = OrderedDict([
                        ("Sequence", sid_name),
                        ("Command", file_name),
                        ("Key_Timestamp",timestamp),
                        ("@timestamp",timestamp)
                    ])

                lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
        else:
            logging.info(u"[{}] {} not found.".format('RunMRU', RunMRU_user_settings_path))

        return lst
