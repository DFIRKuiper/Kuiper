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
import struct

class StreamMRU():
    def __init__(self,prim_hive,log_files):
        self.prim_hive = prim_hive
        self.log_files = log_files

    def run(self):
        "use the NTUSER.dat hive to get the result"
        StreamMRU_user_settings_path = u'Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\StreamMRU'
        hive = get_hive(self.prim_hive,self.log_files)
        StreamMRU_user_settings_key = hive.find_key(StreamMRU_user_settings_path)
        print('Found a key: {}'.format(StreamMRU_user_settings_key.path()))
        if StreamMRU_user_settings_key:
            sid_key_values = iter(StreamMRU_user_settings_key.values())
            timestamp = StreamMRU_user_settings_key.last_written_timestamp().isoformat()
            counter =0
            while True:
                try:
                    value = next(sid_key_values)
                except StopIteration:
                    break
                except Exception as error:
                    logging.error(u"Error getting next value: {}".format(error))
                    continue

                sid_name = value.name()
                data = value.data()
                dump = RegistryHelpers.HexDump(value.data())
                counter = counter +1
                dx = struct.unpack(data)

                print (dx)
                # f= open(str(counter)+".bin","wb")
                # f.write(data)
                # counter = counter +1



                # offset_in_mru_data = 0
                # previous_mru_data = ''
                # for i in range(len(data)):
                #     try:
                #         offset_in_mru_data = i
                #         size, = struct.unpack('H', data[offset_in_mru_data:offset_in_mru_data+2])
                #         if size == 0: # invalid entry - no data
                #             pass
                #     except:
                #       pass
                #print (size)
                #mru_type_value = data[offset_in_mru_data]
                # data_segment = data[offset_in_mru_data:offset_in_mru_data + size]
                # print (data_segment)

                #file_name = strip_control_characters(value.data())

                # record = OrderedDict([
                #         ("_plugin", u"StreamMRU"),
                #         ("Sequence", sid_name),
                #         ("Command", file_name),
                #         ("key_last_written_timestamp",timestamp),
                #     ])
                #
                # print(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
        # else:
        #     logging.info(u"[{}] {} not found.".format('StreamMRU', StreamMRU_user_settings_path))
