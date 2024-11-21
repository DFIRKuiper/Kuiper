import json
import logging
from lib.helper import ComplexEncoder
from lib.helper import strip_control_characters
from yarp import *

Entry = {"@timestamp": "N/A", "Launch String": "N/A", "Category": "Winlogon", "Path": "N/A"}
class Winlogon():
    def __init__(self,prim_hive):
        self.prim_hive = prim_hive
        
    def run(self):
        lst_json = []
        lst_csv = []
        CLSID = []
        Launch_String = []
        "use the SOFTWARE && SYSTEM && Ntuser hive to get the result"
        hive = Registry.RegistryHive(open(self.prim_hive, 'rb'))
        REG_Path_G1 = [ 'Microsoft\Windows\CurrentVersion\Authentication\Credential Providers',
                        'Microsoft\Windows\CurrentVersion\Authentication\Credential Provider Filters',
                        'Microsoft\Windows\CurrentVersion\Authentication\PLAP Providers',]
        
        REG_Path_G2 = [u'ControlSet001\\Control\\BootVerificationProgram',
                       u'\\SOFTWARE\\Policies\\Microsoft\\Windows\\Control Panel\\Desktop',
                       u'\\Control Panel\Desktop']
        SK_Name_G2 = ['ImagePath', 'Scrnsave.exe', 'Scrnsave.exe']
        ##########
        ###Group 1
        ##########
        for p in REG_Path_G1:
            Key = hive.find_key(p)
            if Key:
                for SK in Key.subkeys():
                    CLSID.append(SK.name())
                    Launch_String.append(p)
            else:
                logging.info(u"[{}] {} not found.".format('Winlogon', p))
        ##########
        ###Group 2
        ##########
        for p, SKN in zip(REG_Path_G2, SK_Name_G2):
            Key = hive.find_key(p)
            if Key:
                for x in Key.values():
                    if x.name() == SKN:
                        Entry["@timestamp"] = Key.last_written_timestamp().isoformat()
                        Entry["Path"] = strip_control_characters(x.data())
                        Entry["Launch String"] = REG_Path_G2
                        lst_json.append(u"{}".format(json.dumps(Entry.copy(), cls=ComplexEncoder)))
                        lst_csv.append(Entry.copy())
        else:
            logging.info(u"[{}] {} not found.".format('Winlogon', p))
        ###############
        ###Get Bin Path
        ###############
        for ID, LS in zip(CLSID, Launch_String):
            CLSID_path = ["Wow6432Node\Classes\CLSID\\" + ID + "\InprocServer32", "Classes\CLSID\\" + ID + "\InprocServer32"]
            for p in CLSID_path:
                Bin_key = hive.find_key(p)
                if Bin_key:
                    for y in Bin_key.values():
                        if y.name() == "":
                            Entry["@timestamp"] = Bin_key.last_written_timestamp().isoformat()
                            Entry["Path"] = strip_control_characters(y.data())
                            Entry["Launch String"] = LS
                            lst_json.append(u"{}".format(json.dumps(Entry.copy(), cls=ComplexEncoder)))
                            lst_csv.append(Entry.copy())          
                else:
                    logging.info(u"[{}] {} not found.".format('Winlogon', Bin_key))

        return lst_json, lst_csv, Entry.keys()
