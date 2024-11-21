import json
import logging
import traceback
from collections import OrderedDict
from lib.helper import convert_datetime
from lib.helper import ComplexEncoder
from lib.helper import strip_control_characters
from lib.hive_yarp import get_hive
from yarp import *
import os

class ProfileList():

    def __init__(self,prim_hive,log_files):
        self.prim_hive = prim_hive
        self.log_files = log_files

    def run(self):
        lst= []
        "use the SOFTWARE hive to get the result"
        ProfileList_user_settings_path = u"Microsoft\\Windows NT\\CurrentVersion\\ProfileList"
        hive = get_hive(self.prim_hive,self.log_files)
        ProfileList_user_settings_key = hive.find_key(ProfileList_user_settings_path)
        # print('Found a key: {}'.format(ProfileList_user_settings_key.path()))
        if ProfileList_user_settings_key:
            for sid_key in ProfileList_user_settings_key.subkeys():
                sid_name = sid_key.name()
                Profile_path = sid_key.value(name=u"ProfileImagePath")
                Profile_data = strip_control_characters(Profile_path.data())
                timestamp = sid_key.last_written_timestamp().isoformat()
                user =  strip_control_characters(os.path.basename(os.path.normpath(Profile_data)))
                record = OrderedDict([
                    ("Path", Profile_data),
                    ("User", user),
                    ("sid", sid_name),
                    ("Key_Timestamp", timestamp),
                    ("@timestamp", timestamp)
                ])

                lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
        else:
            logging.info(u"[{}] {} not found.".format('ProfileList', ProfileList_user_settings_path))

        return lst
