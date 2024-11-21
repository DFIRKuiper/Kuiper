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


class Sysinternals():

    def __init__(self,prim_hive,log_files):
        self.prim_hive = prim_hive
        self.log_files = log_files

    def run(self):
        lst = []
        "use the NATUSER.dat hive to get the result"
        #Software\\Classes\\
        Sysinternals_user_settings_path = u'\\Software\\Sysinternals'
        hive = get_hive(self.prim_hive,self.log_files)
        Sysinternals_user_settings_key = hive.find_key(Sysinternals_user_settings_path)
        if Sysinternals_user_settings_key:
            for sid_key in Sysinternals_user_settings_key.subkeys():
                Application_name = sid_key.name()
                timestamp = sid_key.last_written_timestamp().isoformat()
                EulaAccepted = sid_key.value(name=u"EulaAccepted")
                if EulaAccepted:
                    EulaAccepted_data = EulaAccepted.data()
                    if EulaAccepted_data == 1:
                        EulaAccepted_data = "True"
                    else:
                        EulaAccepted_data ="False"
                else:
                    EulaAccepted_data ="None"

                record = OrderedDict([
                        ("Application_Name", Application_name),
                        ("Eula_Accepted", EulaAccepted_data),
                        ("Accepted_TimeStamp",timestamp),
                        ("@timestamp",timestamp),
                    ])

                lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))

        else:
            logging.info(u"[{}] {} not found.".format('Sysinternals', Sysinternals_user_settings_path))

        return lst
