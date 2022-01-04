import json
import logging
import traceback
from collections import OrderedDict
from lib.helper import convert_datetime
from lib.helper import ComplexEncoder
from lib.helper import strip_control_characters
from lib.hive_yarp import get_hive
from yarp import *


class InstalledApp():

    def __init__(self,prim_hive,log_files):
        self.prim_hive = prim_hive
        self.log_files = log_files

    def run(self):
        lst = []
        "use the SOFTWARE hive to get the result"
        InstalledApp_user_settings_path = u"Microsoft\\Windows\\CurrentVersion\\App Paths"
        hive = get_hive(self.prim_hive,self.log_files)
        InstalledApp_user_settings_key = hive.find_key(InstalledApp_user_settings_path)
        # print('Found a key: {}'.format(InstalledApp_user_settings_key.path()))
        if InstalledApp_user_settings_key:
            for sid_key in InstalledApp_user_settings_key.subkeys():
                sid_name = sid_key.name()
                timestamp = sid_key.last_written_timestamp().isoformat()
                Path = sid_key.value(name=u"Path")
                if Path:
                    Path_data = strip_control_characters(Path.data())
                else:
                    Path_data =""
                record = OrderedDict([
                        ("Application_Name", sid_name),
                        ("InstalledApp_date",timestamp),
                        ("Path", Path_data),
                        ("@timestamp",timestamp),
                    ])

                lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
        else:
            logging.info(u"[{}] {} not found.".format('Bam', bam_user_settings_path))

        return lst
