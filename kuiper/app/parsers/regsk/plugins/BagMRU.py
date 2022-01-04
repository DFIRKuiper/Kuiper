import json
import logging
import traceback
from collections import OrderedDict
from lib.helper import convert_datetime
from lib.helper import ComplexEncoder
from lib.hive_yarp import get_hive
from yarp import *

import struct
class BagMRU():

    def __init__(self,prim_hive,log_files):
        self.prim_hive = prim_hive
        self.log_files = log_files

    def run(self):
        lst= []
        "This uses useclass.data"
        BagMRU_user_settings_path = u"Local Settings\\Software\\Microsoft\\Windows\\Shell\\BagMRU"
        hive = get_hive(self.prim_hive,self.log_files)
        BagMRU_user_settings_key = hive.find_key(BagMRU_user_settings_path)
        if BagMRU_user_settings_key:
            for sid_key in BagMRU_user_settings_key.values():
                sid_name = sid_key.name()
                data = sid_key.data()
                if "MRUListEx" == sid_name or "NodeSlot" == sid_name or "NodeSlots"  == sid_name:
                    pass
                else:
                    buf = sid_key.data()
                    #data = buf[::2][:buf[::2].find(b'\x00')].decode()
                    print ("_"*100)
                    dd = RegistryHelpers.HexDump(buf)
                    print(dd)

                    # block = SHITEMLIST(buf, 0x0, False)
                    # offset = 0x10
                    #
                    #
                    # for i in len(data):
                    #     o = i + 2
                    #     dd = struct.unpack_from("<H", data, o)[0]
                    #     print (dd)
                        #size = block.unpack_word(offset)
                        # if size == 0:
                        #     break
                        # elif size < 0x15:
                        #     pass
                        # else:
                        #     item = block.get_item(offset)
                    #print (item)



                # version_value = sid_key.value(name=u"Version")
                # version = None
                # if version_value:
                #     version = version_value.data()
                #
                # sequence_value = sid_key.value(name=u"SequenceNumber")
                # sequence = None
                # if sequence_value:
                #     sequence = version_value.data()

                # We can have an issue with iterating values so we will take it one
                # at a time to try and catch errors.
                # sid_key_values = iter(sid_key.values())
                #
                # while True:
                #     try:
                #         value = next(sid_key_values)
                #     except StopIteration:
                #         break
                #     except Exception as error:
                #         logging.error(u"Error getting next value: {}".format(error))
                #         continue
                #
                #     value_name = value.name()
                #     value_data = value.data_raw()
                #
                #     if value_name not in [u"Version", u"SequenceNumber"]:
                #         timestamp = convert_datetime(value_data[0:8])
                #
                #         record = OrderedDict([
                #             ("_plugin", u"BagMRU"),
                #             ("name", value_name),
                #             ("timestamp", timestamp),
                #             ("sid", sid_name),
                #             ("version", version),
                #             ("sequence", sequence)
                #         ])
                #
                #         print(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
        else:
            logging.info(u"[{}] {} not found.".format('BagMRU', BagMRU_user_settings_path))
