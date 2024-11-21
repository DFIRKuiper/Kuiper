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


class ShellExtensions():

    def __init__(self,prim_hive,log_files):
        self.prim_hive = prim_hive
        self.log_files = log_files

    def run(self):
        lst =[]
        "use the SOFTWARE hive to get the result"
        ShellExtensions_user_settings_path = u'Microsoft\\Windows\\CurrentVersion\\Shell Extensions\\Approved'
        
        hive = get_hive(self.prim_hive,self.log_files)
        ShellExtensions_user_settings_key = hive.find_key(ShellExtensions_user_settings_path)
        if ShellExtensions_user_settings_key:
            sid_key_values = iter(ShellExtensions_user_settings_key.values())
            timestamp = ShellExtensions_user_settings_key.last_written_timestamp().isoformat()
            while True:
                

                try:
                    value = next(sid_key_values)
                except StopIteration:
                    break
                except Exception as error:
                    logging.error(u"Error getting next value: {}".format(error))
                    continue
                
                sid_name= value.name()
                data    = value.data()
                if isinstance(data, bytes):
                    pos = data.find(b'\x00\x00') +1
                    file_name = strip_control_characters(data[:pos].decode('utf-16'))
                else:
                    file_name = strip_control_characters(data)

                record = OrderedDict([
                        ("sid", sid_name),
                        ("File Name", file_name),
                        ("key_last_written_timestamp",timestamp),
                        ("@timestamp",timestamp)
                    ])

                lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
        else:
            logging.info(u"[{}] {} not found.".format('ShellExtensions', ShellExtensions_user_settings_path))

        return lst
