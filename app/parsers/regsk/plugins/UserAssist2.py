import json
import codecs
import struct
from collections import OrderedDict
from lib.helper import ComplexEncoder
from lib.helper import convert_datetime
from lib.hive_yarp import get_hive
from yarp import *
import datetime
# from yarp import Registry

class UserAssist:
    def __init__(self, prim_hive,log_files):
        self.prim_hive =prim_hive
        self.log_files = log_files
# registry_manager
    def run(self):
        # for reg_handler in registry_manager.iter_registry_handlers(name=u'NTUSER.DAT'):

        hive = get_hive(self.prim_hive,self.log_files)
        user_assist_key = hive.find_key(u'Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\UserAssist')
        if user_assist_key is not None:
            lst =[]
            for guid_key in user_assist_key.subkeys():
                guid_key_name = guid_key.name()
                count_key = guid_key.subkey(u"Count")
                dat_key =guid_key.last_written_timestamp().isoformat()
                if count_key is not None:
                    for value in count_key.values():
                        value_name = value.name()
                        value_name_decoded = codecs.encode(value_name, 'rot_13')
                        value_data = value.data()
                        count = None
                        win =""
                        if len(value_data) == 16:
                            count = struct.unpack("<I",value_data[4:8])[0]
                            count -= 5
                            record = OrderedDict([
                                ("_plugin", u"UserAssist"),
                                ("guid", guid_key_name),
                                ("name", value_name_decoded),
                                ("count", count),
                                ("@timestamp",dat_key)
                            ])
                            lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
                        elif len(value_data) == 72:
                            count = struct.unpack("<I", value_data[4:8])[0]
                            date_time = struct.unpack("<q", value_data[60:68])[0]
                            new_datetime =convert_datetime(date_time)
                            if new_datetime == "1601-01-01T00:00:00":
                                new_datetime = dat_key
                            record = OrderedDict([
                                ("guid", guid_key_name),
                                ("name", value_name_decoded),
                                ("count", count),
                                ("key_creation_time",dat_key),
                                ("@timestamp",new_datetime)
                            ])
                            lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
                        else:
                            pass
            return lst
        else:
            return None
