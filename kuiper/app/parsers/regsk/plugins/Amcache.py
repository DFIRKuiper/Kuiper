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
        Amcache_user_settings_Apps_path = u"root\\InventoryApplication"
        Amcache_win10_drivers_path = u"root\\InventoryDriverBinary"
        Amcache_win10_shortcut_path = u"root\\InventoryApplicationShortcut"
        Amcache_win7_user_settings_path = u"root\\File"
        Amcache_win7_user_settings_Apps_path = u"root\\Programs"
        Amcache_user_settings_key = hive.find_key(Amcache_user_settings_path)
        Amcache_user_settings_Apps_key = hive.find_key(Amcache_user_settings_Apps_path)
        Amcache7_user_settings_key = hive.find_key(Amcache_win7_user_settings_path)
        Amcache7_user_settings_Apps_key = hive.find_key(Amcache_win7_user_settings_Apps_path)
        Amcache_win10_drivers_key = hive.find_key(Amcache_win10_drivers_path)
        Amcache_win10_shortcut_key = hive.find_key(Amcache_win10_shortcut_path)
        if Amcache_user_settings_key :
            MappedApps ={}
            if Amcache_user_settings_Apps_key:
                for sid_key in Amcache_user_settings_Apps_key.subkeys():
                    sid_key_values = iter(sid_key.values())
                    key =""

                    while True:
                        try:
                            value = next(sid_key_values)
                        except StopIteration:
                            break
                        except Exception as error:
                            logging.error(u"Error getting next value: {}".format(error))
                            continue
                        value_name = value.name()
                        if value_name == "ProgramId":
                            key = strip_control_characters(str(value.data()))
                        elif value_name == "Name":
                            val = strip_control_characters(str(value.data()))
                            MappedApps[key] = val
                            continue
                   
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
                record["EntryType"]= strip_control_characters(str("File"))
                while True:
                    try:
                        value = next(sid_key_values)
                    except StopIteration:
                        break
                    except Exception as error:
                        logging.error(u"Error getting next value: {}".format(error))
                        continue

                    value_name = value.name()
                    names = value_name
                    try:
                        names =win10_amache_mapping[value_name]
                    except Exception as error:
                        pass
                    data =value.data()

                    record[names]= strip_control_characters(str(data))
                record["@timestamp"] = key_time
                
                try:
                    if record["Sha1"].startswith("0000"):
                        sha1 = record["Sha1"]
                        record["Sha1"]= sha1[4:]
                except Exception as error:
                        pass
                try:
                    fields_count = len(record) - 1 # -1 for the EntryType added above
                    record["FieldsCount"]= strip_control_characters(str(fields_count))
                except Exception as error:
                    record["FieldsCount"]= strip_control_characters(str("-1"))
                    pass
                try:
                    if record["ProgramId"] in MappedApps:
                        record["InstalledApp"] = strip_control_characters(str(MappedApps[record["ProgramId"]]))
                    else:
                        record["InstalledApp"] = strip_control_characters(str("Unassociated"))
                except Exception as error:
                        record["InstalledApp"] = strip_control_characters(str("Unassociated"))
                        pass
                lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))

            if Amcache_win10_drivers_key:
                win10_amache_drivers_mapping={
                    "DriverName"        :"DriverName",
                    "Inf"               :"Inf",
                    "DriverVersion"     :"DriverVersion",
                    "Product"           :"Product",
                    "ProductVersion"    :"ProductVersion",
                    "WdfVersion"        :"WdfVersion",
                    "DriverCompany"     :"CompanyName",
                    "DriverPackageStrongName" :"PackageName",
                    "Service"           :"Service",
                    "DriverInBox"       :"DriverInBox",
                    "DriverSigned"      :"DriverSigned",
                    "DriverIsKernelMode":"DriverIsKernelMode",
                    "DriverId"          :"Sha1",
                    "DriverLastWriteTime":"DriverLastWriteTime",
                    "DriverType"        :"DriverType",
                    "DriverTimeStamp"   :"DriverTimeStamp",
                    "DriverCheckSum"    :"DriverCheckSum",
                    "ImageSize"         :"Size",
                    }
                    #Driver Mapping Res: https://crazymax.dev/WindowsSpyBlocker/assets/MSWin10_GDPR_Compliance.pdf,file:///C:/Users/nalsabti/Downloads/Windows%207-8.1%20Appraiser%20events%20and%20fields.pdf
                    # "define DRIVER_MAP_DRIVER_TYPE_PRINTER" = 1, #0x0001
                    # "define DRIVER_MAP_DRIVER_TYPE_KERNEL" = 2,  #0x0002
                    # "define DRIVER_MAP_DRIVER_TYPE_USER" = 4, #0x0004
                    # "define DRIVER_MAP_DRIVER_IS_SIGNED" = 8,  #0x0008
                    # "define DRIVER_MAP_DRIVER_IS_INBOX" = 16, #0x0010 
                    # "define DRIVER_MAP_DRIVER_IS_SELF_SIGNED" = 32, #0x0020
                    # "define DRIVER_MAP_DRIVER_IS_WINQUAL" = 64, #0x0040
                    # "define DRIVER_MAP_DRIVER_IS_CI_SIGNED" = 128,  #0x0080
                    # "define DRIVER_MAP_DRIVER_HAS_BOOT_SERVICE" =256,  #0x0100
                    # "define DRIVER_MAP_DRIVER_TYPE_I386" = 65536, #0x10000
                    # "define DRIVER_MAP_DRIVER_TYPE_IA64" = 131072, #0x20000
                    # "define DRIVER_MAP_DRIVER_TYPE_AMD64" = 262144, #0x40000
                    # "define DRIVER_MAP_DRIVER_TYPE_ARM"  =  1048576, #0x100000
                    # "define DRIVER_MAP_DRIVER_TYPE_THUMB" = 2097152, #0x200000
                    # "define DRIVER_MAP_DRIVER_TYPE_ARMNT" =  4194304 #0x400000
                    # "define DRIVER_MAP_DRIVER_IS_TIME_STAMPED" = 8388608 #0x800000 
                driver_type_mapping = {
                        8388608 : ["IsTimeStamped",["True", "False"]],
                        4194304 : ["DriverTypeMapped",["ARMNT"]],
                        2097152 : ["DriverTypeMapped",["THUMB"]],
                        1048576 : ["DriverTypeMapped",["ARM"]],
                        262144  : ["DriverTypeMapped",["AMD64"]],
                        131072  : ["DriverTypeMapped",["IA64"]],
                        65536   : ["DriverTypeMapped",["I386"]],
                        256     : ["BootService",["True", "False"]],
                        128     : ["Is_CI_Signed",["True", "False"]],
                        64      : ["IsWINQUAL",["True", "False"]],
                        32      : ["IsSelfSigned",["True", "False"]],
                        16      : ["IsInboxDriver",["True", "False"]],
                        8       : ["IsSigned",["True", "False"]],
                        4       : ["DriverUserMode",["True"]],
                        2       : ["DriverKernalMode",["True"]],
                        1       : ["PrinterDriver",["True"]],
                    }
                driver_type_ints = [8388608,4194304,2097152,1048576,262144,131072,65536,256,128,64,32,16,8,4,2,1]

                for sid_key in Amcache_win10_drivers_key.subkeys():
                    dirverFullPath = sid_key.name()
                    sid_key_values = iter(sid_key.values())
                    key_time = sid_key.last_written_timestamp().isoformat()
                      
                    record = OrderedDict([
                    ])
                    record["EntryType"]= strip_control_characters(str("Drive"))
                    record['Path'] = dirverFullPath
                    while True:
                        try:
                            value = next(sid_key_values)
                        except StopIteration:
                            break
                        except Exception as error:
                            logging.error(u"Error getting next value: {}".format(error))
                            continue

                        value_name = value.name()
                        names = value_name
                        try:
                            names =win10_amache_drivers_mapping[value_name]
                        except Exception as error:
                            pass
                        data =value.data()

                        record[names]= strip_control_characters(str(data))
                        # Breakdown and map driver type
                        try:
                            if names == "DriverType":
                                OredType = int(data)
                                for i in driver_type_ints:
                                    val = driver_type_mapping[i][1][0]
                                    if (OredType & i ==i):
                                        record[driver_type_mapping[i][0]]= strip_control_characters(str(val))
                                    elif (len(driver_type_mapping[i][1])>1):
                                        record[driver_type_mapping[i][0]]= strip_control_characters(driver_type_mapping[i][1][1])
                        except Exception as error:
                           pass


                    record["@timestamp"] = key_time
                    try:
                        record["DriverLastWriteTime"]= datetime.datetime.strptime(record["DriverLastWriteTime"],'%m/%d/%Y %H:%M:%S').isoformat()
                    except Exception as error:
                        pass
                    try:
                        record["DriverTimeStamp"]= datetime.datetime.fromtimestamp(int(record["DriverTimeStamp"])).isoformat()
                    except Exception as error:
                        pass
                    try:
                        if record["Sha1"].startswith("0000"):
                            sha1 = record["Sha1"]
                            record["Sha1"]= sha1[4:]
                    except Exception as error:
                            pass
                    lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
            if Amcache_win10_shortcut_key:
                for sid_key in Amcache_win10_shortcut_key.subkeys():
                    sid_key_values = iter(sid_key.values())
                    key_time = sid_key.last_written_timestamp().isoformat()
                    win10_amache_shortcut_mapping={
                    "ShortcutPath"         :"Path",
                    }
                    record = OrderedDict([
                     ])
                    record["EntryType"]= strip_control_characters(str("LNK"))
                    while True:
                        try:
                            value = next(sid_key_values)
                        except StopIteration:
                            break
                        except Exception as error:
                            logging.error(u"Error getting next value: {}".format(error))
                            continue

                        value_name = value.name()
                        names = value_name
                        try:
                            names =win10_amache_shortcut_mapping[value_name]
                        except Exception as error:
                            pass
                        data =value.data()

                        record[names]= strip_control_characters(str(data))
                    record["@timestamp"] = key_time
                
                    lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
            return lst


        elif Amcache7_user_settings_key:
            MappedApps ={}
            if Amcache7_user_settings_Apps_key:
                for sid_key in Amcache7_user_settings_Apps_key.subkeys():
                    sid_key_values = iter(sid_key.values())
                    key =sid_key.name()
                    while True:
                        try:
                            value = next(sid_key_values)
                        except StopIteration:
                            break
                        except Exception as error:
                            logging.error(u"Error getting next value: {}".format(error))
                            continue
                        value_name = value.name()
                        if value_name == '0':
                            val = strip_control_characters(str(value.data()))
                            MappedApps[key] = val
                            continue
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
                    record["EntryType"]= strip_control_characters(str("File"))
                    while True:
                        try:
                            value = next(sid_key_values)
                        except StopIteration:
                            break
                        except Exception as error:
                            logging.error(u"Error getting next value: {}".format(error))
                            continue

                        value_name = value.name()
                        names = value_name
                        try:
                            names =win8_amcache_mapping[value_name]
                        except Exception as error:
                            pass    
                        data =value.data()
                        if "time" in names:
                            if "linker_compile_time" in names:
                                data = datetime.datetime.fromtimestamp(data)
                            else:
                                data = convert_datetime(data)

                        record[names]= strip_control_characters(str(data))

                    if len(record) == '0':
                        continue
                    record["@timestamp"] = key_time
                    try:
                      if record["Sha1"].startswith("0000"):
                        sha1 = record["Sha1"]
                        record["Sha1"]= sha1[4:]
                    except Exception as error:
                            pass
                    try:
                        fields_count = len(record) - 1 # -1 for the EntryType added above
                        record["FieldsCount"]= strip_control_characters(str(fields_count))
                    except Exception as error:
                        record["FieldsCount"]= strip_control_characters(str("-1"))
                        pass
                    try:
                        if record["ProgramId"] in MappedApps:
                            record["InstalledApp"] = strip_control_characters(str(MappedApps[record["ProgramId"]]))
                        else:
                            record["InstalledApp"] = strip_control_characters(str("Unassociated"))
                    except Exception as error:
                        record["InstalledApp"] = strip_control_characters(str("Unassociated"))
                        pass

                    lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
            return lst

        else:
            logging.info(u"[{}] {} not found.".format('Amcache', Amcache_user_settings_key))
