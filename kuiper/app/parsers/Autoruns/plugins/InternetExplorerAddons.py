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


class InternetExplorerAddons():
    def __init__(self,prim_hive,log_files):
        self.prim_hive = prim_hive
        self.log_files = log_files
        
    def run(self):
        lst = []
        CLSID = []
        Launch_String = []
        "use the SOFTWARE && Ntuser hive to get the result"
        hive = get_hive(self.prim_hive,self.log_files)
        REG_Path_G1 = [ 'Wow6432Node\Microsoft\Windows\CurrentVersion\Explorer\Browser Helper Objects',
                        'Microsoft\Windows\CurrentVersion\Explorer\Browser Helper Objects',
                        'Wow6432Node\Microsoft\Internet Explorer\Explorer Bars',
                        'Microsoft\Internet Explorer\Explorer Bars',
                        'Wow6432Node\Microsoft\Internet Explorer\Extensions',
                        'Microsoft\Internet Explorer\Extensions',
                        u'\\Software\Wow6432Node\Microsoft\Internet Explorer\Explorer Bars',
                        u'\\Software\Microsoft\Internet Explorer\Explorer Bars',
                        u'\\Software\Wow6432Node\Microsoft\Internet Explorer\Extensions',
                        u'\\Software\Microsoft\Internet Explorer\Extensions']

        REG_Path_G2 = [ 'WOW6432Node\Microsoft\Internet Explorer\Toolbar',
                        'Microsoft\Internet Explorer\Toolbar',
                        u'\\Software\\Microsoft\\Internet Explorer\\UrlSearchHooks']
        for p in REG_Path_G1:
            Key = hive.find_key(p)
            if Key:
                for SK in Key.subkeys():
                    if SK.name().startswith('{'):
                        CLSID.append(SK.name())
                        Launch_String.append(p)
            else:
                logging.info(u"[{}] {} not found.".format('Explorer', p))
        #############        
        # Group 2
        #############
        for p in REG_Path_G2:
            Key = hive.find_key(p)
            if Key:
                for x in Key.values():
                    CLSID.append(x.name())
                    Launch_String.append(p)
            else:
                logging.info(u"[{}] {} not found.".format('Explorer', p))
        #############        
        # Get Path && Description From CLSID
        #############
        for ID, LS in zip(CLSID, Launch_String):
            CLSID_path = ["Wow6432Node\Classes\CLSID\\" + ID, "Classes\CLSID\\" + ID]
            for p in CLSID_path:
                Bin_key = hive.find_key(p)
                if Bin_key:
                    for x in Bin_key.values():
                        Description = strip_control_characters(x.data())
                    for SK in Bin_key.subkeys():
                        if SK.name() == 'InprocServer32':
                            for y in SK.values():
                                TS = SK.last_written_timestamp().isoformat()
                                if y.name()=='':
                                    Path = strip_control_characters(y.data())
                                record = OrderedDict([
                                    ("@timestamp",TS),
                                    ("Launch String", LS),
                                    ("Category", "Explorer"),
                                    ("Path", Path),
                                    ("Description", Description)
                                ])
                            lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
                else:
                    logging.info(u"[{}] {} not found.".format('InternetExplorerAddons', Bin_key))

        return lst
