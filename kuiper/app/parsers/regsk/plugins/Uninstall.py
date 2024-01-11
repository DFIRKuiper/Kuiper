import json
import logging
import traceback
from collections import OrderedDict
from lib.helper import convert_datetime
from lib.helper import ComplexEncoder
from lib.helper import strip_control_characters
from lib.hive_yarp import get_hive
from yarp import *


class Uninstall():
    def __init__(self,prim_hive,log_files):
        self.prim_hive = prim_hive
        self.log_files = log_files

    def run(self):
        lst = []
        "use the SOFTWARE hive to get the result"
        Uninstall_user_settings_path = u"Microsoft\\Windows\\CurrentVersion\\Uninstall"
        hive = get_hive(self.prim_hive,self.log_files)
        Uninstall_user_settings_key = hive.find_key(Uninstall_user_settings_path)
        # print('Found a key: {}'.format(Uninstall_user_settings_key.path()))
        if Uninstall_user_settings_key:
            for sid_key in Uninstall_user_settings_key.subkeys():
                sid_name = sid_key.name()
                timestamp = sid_key.last_written_timestamp().isoformat()
                #try:
                DisplayName = sid_key.value(name=u"DisplayName")
                if DisplayName:
                    DisplayName_data = strip_control_characters(DisplayName.data())
                else:
                    DisplayName_data =""

                DisplayVersion = sid_key.value(name=u"DisplayVersion")
                if DisplayVersion:
                    DisplayVersion_data = strip_control_characters(DisplayVersion.data())
                else:
                    DisplayVersion_data =""

                InstallDate = sid_key.value(name=u"InstallDate")
                if InstallDate:
                    InstallDate_data = strip_control_characters(InstallDate.data())

                else:
                    InstallDate_data =""

                InstallLocation = sid_key.value(name=u"InstallLocation")
                if InstallLocation:
                    InstallLocation_data = strip_control_characters(InstallLocation.data())
                else:
                    InstallLocation_data =""

                InstallSource= sid_key.value(name=u"InstallSource")
                if InstallSource:
                    InstallSource_data = strip_control_characters(InstallSource.data())
                else:
                    InstallSource_data =""

                ModifyPath = sid_key.value(name=u"ModifyPath")
                if ModifyPath:
                    ModifyPath_data = strip_control_characters(ModifyPath.data())
                else:
                    ModifyPath_data =""

                Publisher = sid_key.value(name=u"Publisher")
                if Publisher:
                    Publisher_data = strip_control_characters(Publisher.data())
                else:
                    Publisher_data=""
                Size = sid_key.value(name=u"Size")
                if Size:
                    Size_data = str(Size.data())
                else:
                    Size_data =""

                URLInfoAbout = sid_key.value(name=u"URLInfoAbout")
                if URLInfoAbout:
                    URLInfoAbout_data = strip_control_characters(URLInfoAbout.data())
                else:
                    URLInfoAbout_data =""

                record = OrderedDict([
                        ("name", sid_name),
                        ("Uninstall_date",timestamp),
                        ("Application_Name", DisplayName_data),
                        ("Version",DisplayVersion_data),
                        ("Install_Date",InstallDate_data),
                        ("Install_Location", InstallLocation_data),
                        ("Install_Source", InstallSource_data),
                        ("Modify_Path", ModifyPath_data),
                        ("Publisher", Publisher_data),
                        ("Size", Size_data),
                        ("URLInfoAbout",URLInfoAbout_data),
                        ("@timestamp",timestamp)


                    ])

                lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
        else:
            logging.info(u"[{}] {} not found.".format('Bam', bam_user_settings_path))

        return lst
