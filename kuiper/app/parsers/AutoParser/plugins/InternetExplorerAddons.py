import json
import logging
from lib.helper import ComplexEncoder
from lib.helper import strip_control_characters
from yarp import *

Entry = {"@timestamp": "N/A", "Launch String": "N/A", "Category": "Internet Explorer Addons", "Name": "N/A"}
class InternetExplorerAddons():
    def __init__(self,prim_hive):
        self.prim_hive = prim_hive
        
    def run(self):
        lst_json = []
        lst_csv = []
        CLSID = []
        Launch_String = []
        "use the SOFTWARE && Ntuser hive to get the result"
        hive = Registry.RegistryHive(open(self.prim_hive, 'rb'))
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
                logging.info(u"[{}] {} not found.".format('Internet Explorer Addons', p))
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
                logging.info(u"[{}] {} not found.".format('Internet Explorer Addons', p))
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
                                if y.name()=='':
                                    Entry["@timestamp"] = SK.last_written_timestamp().isoformat()
                                    Entry["Path"] = strip_control_characters(y.data())
                                    Entry["Launch String"] = LS
                                    Entry["Description"] = Description
                                    lst_json.append(u"{}".format(json.dumps(Entry.copy(), cls=ComplexEncoder)))
                                    lst_csv.append(Entry.copy())                   
                else:
                    logging.info(u"[{}] {} not found.".format('Internet Explorer Addons', Bin_key))

        return lst_json, lst_csv, Entry.keys()
