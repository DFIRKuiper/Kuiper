import json
import logging
import traceback
from collections import OrderedDict
from lib.helper import convert_datetime
from lib.helper import ComplexEncoder
from lib.helper import strip_control_characters
from lib.hive_yarp import get_hive
from yarp import *


class InstalledComponents():
    _plugin_name = u"InstalledComponents"

    def __init__(self,prim_hive,log_files):
        self.prim_hive = prim_hive
        self.log_files = log_files

    def run(self):
        lst= []
        "use the SOFTWARE hive to get the result"
        InstalledComponents_user_settings_path = [u'Microsoft\\Active Setup\\Installed Components',u'Wow6432Node\\Microsoft\\Active Setup\\Installed Components']
        hive = get_hive(self.prim_hive,self.log_files)
        for path in InstalledComponents_user_settings_path:
            InstalledComponents_user_settings_key = hive.find_key(path)
            if InstalledComponents_user_settings_key:
                for sid_key in InstalledComponents_user_settings_key.subkeys():
                    sid_name = sid_key.name()
                    timestamp = sid_key.last_written_timestamp().isoformat()
                    IsInstalled = sid_key.value(name=u"IsInstalled")
                    if IsInstalled:
                        IsInstalled_data = IsInstalled.data()
                    else:
                        IsInstalled_data ="None"

                    DontAsk = sid_key.value(name=u"DontAsk")
                    if DontAsk:
                        DontAsk_data = DontAsk.data()
                    else:
                        DontAsk_data ="None"

                    Enabled = sid_key.value(name=u"Enabled")
                    if Enabled:
                        Enabled_data = Enabled.data()
                    else:
                        Enabled_data ="None"

                    Locale = sid_key.value(name=u"Locale")
                    if Locale:
                        Locale_data = strip_control_characters(Locale.data())
                    else:
                        Locale_data ="None"

                    LocalizedName = sid_key.value(name=u"LocalizedName")
                    if LocalizedName:
                        LocalizedName_data = strip_control_characters(LocalizedName.data())
                    else:
                        LocalizedName_data ="None"

                    StubPath = sid_key.value(name=u"StubPath")
                    if StubPath:
                        StubPath_data = strip_control_characters(StubPath.data())
                    else:
                        StubPath_data ="None"

                    Version = sid_key.value(name=u"Version")
                    if Version:
                        Version_data = strip_control_characters(Version.data())
                    else:
                        Version_data ="None"

                    ComponentID = sid_key.value(name=u"ComponentID")
                    if ComponentID:
                        ComponentID_data = strip_control_characters(ComponentID.data())
                    else:
                        ComponentID_data ="None"

                    record = OrderedDict([
                            ("sid", sid_name),
                            ("last_written_timestamp",timestamp),
                            ("ComponentID", ComponentID_data),
                            ("Version", Version_data),
                            ("StubPath", StubPath_data),
                            ("LocalizedName", LocalizedName_data),
                            ("Locale", Locale_data),
                            ("Enabled", Enabled_data),
                            ("DontAsk", DontAsk_data),
                            ("IsInstalled", IsInstalled_data),
                            ("@timestamp",timestamp)


                        ])

                    lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
        else:
            logging.info(u"[{}] {} not found.".format('InstalledComponents', InstalledComponents_user_settings_path))

        return lst
