import json
import logging
import traceback
from collections import OrderedDict
from lib.helper import convert_datetime,from_fat
from lib.helper import ComplexEncoder
from lib.helper import strip_control_characters
from lib.hive_yarp import get_hive
import datetime
from yarp import *


class Amcache():

    def __init__(self,prim_hive,log_files):
        self.prim_hive = prim_hive
        self.log_files = log_files


    def run(self):
        lst =[]
        hive = get_hive(self.prim_hive,self.log_files)
        Amcache_user_settings_path = u"root\\InventoryApplicationFile"
        Amcache_win7_user_settings_path = u"root\\File"
        Amcache_user_settings_key = hive.find_key(Amcache_user_settings_path)
        Amcache7_user_settings_key = hive.find_key(Amcache_win7_user_settings_path)
        if Amcache_user_settings_key :
            for sid_key in Amcache_user_settings_key.subkeys():
                sid_key_values = iter(sid_key.values())
                key_time = sid_key.last_written_timestamp().isoformat()
                win10_amache_mapping={
                "ProgramId"         :"ProgramId",
                "LongPathHash"      :"LongPathHash",
                "IsOsComponent"     :"IsOsComponent",
                "Usn"               :"Usn",
                "LowerCaseLongPath" :"Path",
                "FileId"            :"Sha1",
                "Name"              :"Name",
                "Publisher"         :"CompanyName",
                "Version"           :"Version",
                "BinFileVersion"    :"BinFileVersion",
                "BinaryType"        :"BinaryType",
                "ProductName"       :"ProductName",
                "ProductVersion"    :"ProductVersion",
                "LinkDate"          :"LinkDate",
                "BinProductVersion" :"BinProductVersion",
                "Size"              :"FileSize",
                "Language"          :"Language",
                "IsPeFile"          :"IsPeFile",
                "OriginalFileName"  :"OriginalFileName",
                "AppxPackageFullName":"AppxPackageFullName",
                "AppxPackageRelativeId":"AppxPackageRelativeId"
                }
                record = OrderedDict([
                ])
                while True:
                    try:
                        value = next(sid_key_values)
                    except StopIteration:
                        break
                    except Exception as error:
                        logging.error(u"Error getting next value: {}".format(error))
                        continue

                    value_name = value.name()
                    names =win10_amache_mapping[value_name]
                    data =value.data()

                    record[names]= strip_control_characters(str(data))
                record["@timestamp"] = key_time
                
                if record["Sha1"].startswith("0000"):
                    sha1 = record["Sha1"]
                    record["Sha1"]= sha1[4:]
                lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
            return lst


        elif Amcache7_user_settings_key:
            win8_amcache_mapping = {
                    '0': 'ProductName',
                    '1': 'CompanyName',
                    '2': 'FileVersionNum',
                    '3': 'Language',
                    '4': 'SwitchBackContext',
                    '5': 'FileVersion',
                    '6': 'FileSize',
                    '7': 'pe_header_hash',
                    '8': 'unknown1',
                    '9': 'pe_header_checksum',
                    'a': 'unknown2',
                    'b': 'unknown3',
                    'c': 'file_description',
                    'd': 'unknown4',
                    'f': 'linker_compile_time',
                    '10': 'unknown5',
                    '11': 'last_modified_timestamp',
                    '12': 'created_timestamp',
                    '15': 'Path',
                    '16': 'unknown6',
                    '17': 'last_modified_timestamp_2',
                    '100': 'ProgramId',
                    '101': 'Sha1'
                }
            for sid_key in Amcache7_user_settings_key.subkeys():
                for sidd_key in sid_key.subkeys():
                    sid_key_values = iter(sidd_key.values())
                    key_time = sidd_key.last_written_timestamp().isoformat()
                    record = OrderedDict([
                    ])
                    while True:
                        try:
                            value = next(sid_key_values)
                        except StopIteration:
                            break
                        except Exception as error:
                            logging.error(u"Error getting next value: {}".format(error))
                            continue

                        value_name = value.name()
                        names =win8_amcache_mapping[value_name]
                        data =value.data()
                        if "time" in names:
                            if "linker_compile_time" in names:
                                data = datetime.datetime.fromtimestamp(data)
                            else:
                                data = convert_datetime(data)

                        record[names]= strip_control_characters(str(data))

                    if len(record) == 0:
                        continue
                    record["@timestamp"] = key_time
                    if record["Sha1"].startswith("0000"):
                        sha1 = record["Sha1"]
                        record["Sha1"]= sha1[4:]
                    lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
            return lst

        else:
            logging.info(u"[{}] {} not found.".format('Amcache', Amcache_user_settings_key))
