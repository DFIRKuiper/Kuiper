import json
import logging
import traceback
from collections import OrderedDict
from lib.helper import convert_datetime
from lib.helper import ComplexEncoder
from lib.hive_yarp import get_hive
from yarp import *
from lib.helper import strip_control_characters

class TimeZoneInformation():

    def __init__(self,prim_hive,log_files):
        self.prim_hive = prim_hive
        self.log_files = log_files

    def run(self):
        lst = []
        TimeZoneInformation_user_settings_path = u"ControlSet001\\Control\\TimeZoneInformation"
        hive = get_hive(self.prim_hive,self.log_files)
        TimeZoneInformation_user_settings_key = hive.find_key(TimeZoneInformation_user_settings_path)
        if TimeZoneInformation_user_settings_key:
            TimeZoneKeyName = TimeZoneInformation_user_settings_key.value(name=u"TimeZoneKeyName")
            TimeZoneKeyName_data = TimeZoneKeyName.data()
            timestamp = TimeZoneInformation_user_settings_key.last_written_timestamp().isoformat()
            record = OrderedDict([
                ("Time Zone", strip_control_characters(TimeZoneKeyName_data)),
                ("Key_Timestamp", timestamp),
                ("@timestamp",timestamp)
            ])

            lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))

        else:
            logging.info(u"[{}] {} not found.".format('TimeZoneInformation', TimeZoneInformation_user_settings_path))

        return lst
