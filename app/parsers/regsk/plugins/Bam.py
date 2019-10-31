import json
import logging
import traceback
from collections import OrderedDict
from lib.helper import convert_datetime
from lib.helper import ComplexEncoder
from lib.hive_yarp import get_hive
from yarp import *


class Bam():

    def __init__(self,prim_hive,log_files):
        self.prim_hive = prim_hive
        self.log_files = log_files

    def run(self):
        lst =[]
        bam_user_settings_path = u"ControlSet001\\Services\\bam\\UserSettings"
        hive = get_hive(self.prim_hive,self.log_files)
        bam_user_settings_key = hive.find_key(bam_user_settings_path)
        if bam_user_settings_key:
            for sid_key in bam_user_settings_key.subkeys():
                sid_name = sid_key.name()
                version_value = sid_key.value(name=u"Version")
                version = None
                if version_value:
                    version = version_value.data()

                sequence_value = sid_key.value(name=u"SequenceNumber")
                sequence = None
                if sequence_value:
                    sequence = version_value.data()

                sid_key_values = iter(sid_key.values())

                while True:
                    try:
                        value = next(sid_key_values)
                    except StopIteration:
                        break
                    except Exception as error:
                        logging.error(u"Error getting next value: {}".format(error))
                        continue

                    value_name = value.name()
                    value_data = value.data_raw()

                    if value_name not in [u"Version", u"SequenceNumber"]:
                        timestamp = convert_datetime(value_data[0:8])

                        record = OrderedDict([
                            ("name", value_name),
                            ("@timestamp", timestamp),
                            ("sid", sid_name),
                            ("version", version),
                            ("sequence", sequence)
                        ])

                        lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
            return lst
        else:
            logging.info(u"[{}] {} not found.".format('Bam', bam_user_settings_path))
