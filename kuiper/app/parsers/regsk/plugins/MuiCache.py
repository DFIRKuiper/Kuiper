import json
import logging
import traceback
from collections import OrderedDict
from lib.helper import convert_datetime
from lib.helper import ComplexEncoder
from lib.hive_yarp import get_hive
from yarp import *


class MuiCache():
    def __init__(self,prim_hive,log_files):
        self.prim_hive = prim_hive
        self.log_files = log_files

    def run(self):
        lst =[]
        MuiCache_user_settings_path = u"\\Local Settings\\Software\\Microsoft\\Windows\\Shell\\MuiCache"
        hive = get_hive(self.prim_hive,self.log_files)

        MuiCache_user_settings_key = hive.find_key(MuiCache_user_settings_path)

        if MuiCache_user_settings_key:
            sid_name = MuiCache_user_settings_key.name()
            sid_key_values = iter(MuiCache_user_settings_key.values())
            timestamp = MuiCache_user_settings_key.last_written_timestamp().isoformat()
            while True:
                try:
                    value = next(sid_key_values)
                except StopIteration:
                    break
                except Exception as error:
                    logging.error(u"Error getting next value: {}".format(error))
                    continue

                value_name = value.name()
                value_data = value.data_raw()

                record = OrderedDict([
                        ("name", value_name),
                        ("sid", sid_name),
                        ("Key_Timestamp", timestamp),
                        ("@timestamp", timestamp)
                    ])

                lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
            return lst
        else:
            logging.info(u"[{}] {} not found.".format('Muicache', MuiCache_user_settings_key))
