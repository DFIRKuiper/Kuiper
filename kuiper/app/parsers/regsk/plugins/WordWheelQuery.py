import json
import logging
import traceback
from collections import OrderedDict
from lib.helper import convert_datetime
from lib.helper import ComplexEncoder
from lib.hive_yarp import get_hive
from yarp import *
from lib.helper import strip_control_characters

class WordWheelQuery():

    def __init__(self,prim_hive,log_files):
        self.prim_hive = prim_hive
        self.log_files = log_files

    def run(self):
        lst = []
        WordWheelQuery_user_settings_path = u"Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\WordWheelQuery"
        hive = get_hive(self.prim_hive,self.log_files)
        WordWheelQuery_user_settings_key = hive.find_key(WordWheelQuery_user_settings_path)
        if WordWheelQuery_user_settings_key:
            #for sid_key in WordWheelQuery_user_settings_key.subkeys():
            sid_key_values = iter(WordWheelQuery_user_settings_key.values())
            while True:
                try:
                    value = next(sid_key_values)
                except StopIteration:
                    break
                except Exception as error:
                    logging.error(u"Error getting next value: {}".format(error))
                    continue

                value_name = value.name()
                url_data =value.data().decode("utf-16")
                timestamp = WordWheelQuery_user_settings_key.last_written_timestamp().isoformat()
                record = OrderedDict([
                    ("Key_Timestamp",timestamp),
                    ("Url_Name", value_name),
                    ("Url", strip_control_characters(url_data)),
                    ("@timestamp",timestamp),
                ])

                lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))

        else:
            logging.info(u"[{}] {} not found.".format('WordWheelQuery', WordWheelQuery_user_settings_path))

        return lst
