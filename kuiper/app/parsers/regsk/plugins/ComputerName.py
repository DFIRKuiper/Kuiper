import json
import logging
import traceback
from collections import OrderedDict
from lib.helper import convert_datetime
from lib.helper import ComplexEncoder
from lib.hive_yarp import get_hive
from yarp import *
from lib.helper import strip_control_characters

class ComputerName():

    def __init__(self,prim_hive,log_files):
        self.prim_hive = prim_hive
        self.log_files = log_files

    def run(self):
        hive = get_hive(self.prim_hive,self.log_files)
        select_key = hive.find_key(u'Select')
        current_path=''
        if select_key:
            current_value = select_key.value(name=u"Current")
            current_path = u"ControlSet{:03d}".format(current_value.data())
        else:
            current_path ='ControlSet001'
        lst = []
        ComputerName_user_settings_path = u"\\".join([current_path,u"Control\\ComputerName\\ComputerName"])
        ComputerName_user_settings_key = hive.find_key(ComputerName_user_settings_path)
        if ComputerName_user_settings_key:
            ComputerName = ComputerName_user_settings_key.value(name=u"ComputerName")
            ComputerName_data = ComputerName.data()
            timestamp = ComputerName_user_settings_key.last_written_timestamp().isoformat()
            record = OrderedDict([
                ("ComputerName", strip_control_characters(ComputerName_data)),
                ("Key_Timestamp", timestamp),
                ("@timestamp",timestamp)
            ])

            lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))

        else:
            logging.info(u"[{}] {} not found.".format('ComputerName', ComputerName_user_settings_path))

        return lst
