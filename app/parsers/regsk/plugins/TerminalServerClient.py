import json
import logging
import traceback
from collections import OrderedDict
from lib.helper import convert_datetime
from lib.helper import ComplexEncoder
from lib.hive_yarp import get_hive
from yarp import *
from lib.helper import strip_control_characters


class TerminalServerClient():

    def __init__(self,prim_hive,log_files):
        self.prim_hive = prim_hive
        self.log_files = log_files

    def run(self):
        lst = []
        TerminalServerClient_user_settings_paths = ['Software\\Microsoft\\Terminal Server Client\\Servers', 'Software\\Microsoft\\Terminal Server Client\\Default']
        for TerminalServerClient_user_settings_path in TerminalServerClient_user_settings_paths:
            hive = get_hive(self.prim_hive,self.log_files)
            TerminalServerClient_user_settings_key = hive.find_key(TerminalServerClient_user_settings_path)
            # print('Found a key: {}'.format(TerminalServerClient_user_settings_key.path()))
            if TerminalServerClient_user_settings_key:
                timestamp = TerminalServerClient_user_settings_key.last_written_timestamp().isoformat()
                if "Servers" in TerminalServerClient_user_settings_path:
                    for sid_key in TerminalServerClient_user_settings_key.subkeys():
                        key_name = sid_key.name()
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
                            UsernameHint = "" if "UsernameHint" != value_name else strip_control_characters(value.data())
                            
                                

                            record = OrderedDict([
                                ("key_timestamp", timestamp),
                                ("IP_Address", key_name),
                                ("User_Name", UsernameHint),
                                ("@timestamp", timestamp)
                            ])
                            lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
                else :
                    sid_key_values = iter(TerminalServerClient_user_settings_key.values())

                    while True:
                        try:
                            value = next(sid_key_values)
                        except StopIteration:
                            break
                        except Exception as error:
                            logging.error(u"Error getting next value: {}".format(error))
                            continue

                        value_name = value.name()
                        value_data = value.data()

                        record = OrderedDict([
                        ("key_timestamp", timestamp),
                            ("@timestamp", timestamp),
                            ("IP_Address", strip_control_characters(value_data)),
                            ("Value_Name", value_name)
                        ])
        #
                        lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))

        else:
            logging.info(u"[{}] {} not found.".format('TerminalServerClient', TerminalServerClient_user_settings_path))
        return lst
