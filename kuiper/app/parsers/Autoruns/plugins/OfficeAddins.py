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


class OfficeAddins():
    def __init__(self,prim_hive,log_files):
        self.prim_hive = prim_hive
        self.log_files = log_files
        
    def run(self):
        lst = []
        CLSID = []
        Launch_String = []
        SubKeys = []
        KeyName = []
        "use the SOFTWARE && Ntuser hive to get the result"
        hive = get_hive(self.prim_hive,self.log_files)
        REG_Path_G1 = [ 'Wow6432Node\Microsoft\Office',
                        'Microsoft\Office']
        REG_Path_G2 = [u'\\SOFTWARE\\Wow6432Node\\Microsoft\\Office test\\Special\\Perf',
                       u'\\SOFTWARE\\Microsoft\\Office test\\Special\\Perf']

        ##########
        ###Group 1
        ##########
        for p in REG_Path_G1:
            Key = hive.find_key(p)
            if Key:
                for SK in Key.subkeys():
                    SubKeys.append(SK.name())
            else:
                logging.info(u"[{}] {} not found.".format('OfficeAddins', p))

        ##########
        ###Group 2
        ##########
        for p in REG_Path_G2:
            Key = hive.find_key(p)
            if Key:
                for x in Key.values():
                    if x.name() == '':
                        TS = Key.last_written_timestamp().isoformat()
                        Path = strip_control_characters(x.data())
                        record = OrderedDict([
                            ("@timestamp",TS),
                            ("Launch String", p),
                            ("Category", "Codecs"),
                            ("Name", x.name()),
                            ("Path", Path)
                            ])
                        lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))  
            else:
                logging.info(u"[{}] {} not found.".format('OfficeAddins', p))

        ##################
        ###GET Key Path G1
        ##################
        for k in SubKeys:
            Key_Path = [ 'Wow6432Node\Microsoft\Office\\' + k + '\Addins', 'Microsoft\Office\\' + k + '\Addins']
            for p in Key_Path:
                key = hive.find_key(p)
                if key:
                    for SK in key.subkeys():
                        KeyName.append(SK.name())
                        Launch_String.append(p)
                else:
                    logging.info(u"[{}] {} not found.".format('OfficeAddins', p))
        ###############
        ###GET CLSID G1
        ###############
        for n in KeyName:
            Key_Path = 'Classes\\' + n + '\CLSID'
            key = hive.find_key(Key_Path)
            if key:
                for x in key.values():
                    if x.name() == '':
                        CLSID.append(strip_control_characters(x.data()))
                        
            else:
                logging.info(u"[{}] {} not found.".format('OfficeAddins', p))
        ##################
        ###GET BIN Path G1
        ##################       
        for ID, LS in zip(CLSID, Launch_String):
            CLSID_path = ["Wow6432Node\Classes\CLSID\\" + ID + "\InprocServer32", "Classes\CLSID\\" + ID + "\InprocServer32"]
            for p in CLSID_path:
                Bin_key = hive.find_key(p)
                if Bin_key:
                    for y in Bin_key.values():
                        if y.name() == "":
                            TS = Bin_key.last_written_timestamp().isoformat()
                            Path = strip_control_characters(y.data())
                            record = OrderedDict([
                                ("@timestamp",TS),
                                ("Launch String", LS),
                                ("Category", "Codecs"),
                                ("Path", Path)
                            ])
                            lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
            
                else:
                    logging.info(u"[{}] {} not found.".format('Codecs', Bin_key))

        return lst
