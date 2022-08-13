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


class ServicesAndDrivers():
    def __init__(self,prim_hive,log_files):
        self.prim_hive = prim_hive
        self.log_files = log_files
        
    def run(self):
        lst = []
        SKN_Driver = []
        SKN_service = []
        "use the SYSTEM && SOFTWARE hive to get the result"
        hive = get_hive(self.prim_hive,self.log_files)
        REG_Path_1 = u'ControlSet001\Services'
        REG_Path_2 = 'Microsoft\Windows NT\CurrentVersion\Font Drivers'
        ##################
        ###Get SK-Names #1
        ##################
        Key = hive.find_key(REG_Path_1)
        if Key:
            for SK in Key.subkeys():
                for x in SK.values():
                    if x.name() == 'Type':
                        if x.data() == 1:
                            SKN_Driver.append(SK.name())
                        if x.data() == 16 or x.data() == 32:
                            SKN_service.append(SK.name())
            else:
                logging.info(u"[{}] {} not found.".format('ServicesAndDrivers', REG_Path_1))
        ##############
        ######Drivers
        ##############
        for n in SKN_Driver:
            Key_Path = u'ControlSet001\Services\\' + n           
            Key = hive.find_key(Key_Path)
            if Key:
                for y in Key.values():
                    if y.name() == 'ImagePath':
                        Path = strip_control_characters(y.data())
                        TS = Key.last_written_timestamp().isoformat()
                        record = OrderedDict([
                            ("@timestamp",TS),
                            ("Launch String", "ControlSet001\Services"),
                            ("Category", "Driver"),
                            ("Name", n),
                            ("Path", Path)
                        ])
                        lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
            else:
                logging.info(u"[{}] {} not found.".format('ServicesAndDrivers', Key_Path))
        ##############
        ######Services
        ##############
        for n in SKN_service:
            Key_Path = u'ControlSet001\Services\\' + n           
            Key = hive.find_key(Key_Path)
            if Key:
                for y in Key.values():
                    if y.name() == 'ImagePath':
                        Path = strip_control_characters(y.data())
                        TS = Key.last_written_timestamp().isoformat()
                        Para_Path = u'ControlSet001\Services\\' + n + '\\Parameters'
                        Key = hive.find_key(Para_Path)
                        if Key:
                            for z in Key.values():
                                if z.name() == 'ServiceDll':
                                    ServiceDll = strip_control_characters(z.data())
                                    record = OrderedDict([
                                        ("@timestamp",TS),
                                        ("Launch String", "ControlSet001\Services"),
                                        ("Category", "Service"),
                                        ("Path", Path),
                                        ("Name", n),
                                        ("Service Dll", ServiceDll)
                                    ])
                                    lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
            else:
                logging.info(u"[{}] {} not found.".format('ServicesAndDrivers', Key_Path))
        ##################
        ###Get Drivers #2
        ##################
        Key = hive.find_key(REG_Path_2)
        if Key:
            for x in Key.values():
                if x.name() != '':
                    Path = strip_control_characters(x.data())
                    TS = Key.last_written_timestamp().isoformat()
                    record = OrderedDict([
                        ("@timestamp",TS),
                        ("Launch String", "Microsoft\Windows NT\CurrentVersion\Font Drivers"),
                        ("Category", "Driver"),
                        ("Path", Path)
                    ])
                    lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
            else:
                logging.info(u"[{}] {} not found.".format('ServicesAndDrivers', REG_Path_2))

        return lst
