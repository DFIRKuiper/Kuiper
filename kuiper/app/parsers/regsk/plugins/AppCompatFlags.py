import json
import logging
import traceback
from collections import OrderedDict
from lib.helper import convert_datetime
from lib.helper import ComplexEncoder
from lib.hive_yarp import get_hive
from yarp import *


class AppCompatFlags():

    def __init__(self,prim_hive,log_files):
        self.prim_hive = prim_hive
        self.log_files = log_files

    def run(self):
        lst= []
        AppCompatFlags_user_settings_path = u"\\Software\\Microsoft\\Windows NT\\CurrentVersion\\AppCompatFlags\\Layers"
        hive = get_hive(self.prim_hive,self.log_files)
        AppCompatFlags_user_settings_key = hive.find_key(AppCompatFlags_user_settings_path)

        if AppCompatFlags_user_settings_key:
            sid_name = AppCompatFlags_user_settings_key.name()
            timestamp = AppCompatFlags_user_settings_key.last_written_timestamp().isoformat()
            sid_key_values = iter(AppCompatFlags_user_settings_key.values())
            while True:
                try:
                    value = next(sid_key_values)
                except StopIteration:
                    break
                except Exception as error:
                    logging.error(u"Error getting next value: {}".format(error))
                    continue

                value_name = value.name()
                value_datax = value.data()

                record = OrderedDict([
                    ("File", value_name),
                    ("Key_Timestamp", timestamp),
                    ("sid", sid_name),
                    ("value", value_datax),
                    ("@timestamp", timestamp),
                ])

                lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
            return lst
        else:
            logging.info(u"[{}] {} not found.".format('AppCompatFlags', AppCompatFlags_user_settings_path))
