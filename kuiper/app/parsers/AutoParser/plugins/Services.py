import json
import logging
from lib.helper import ComplexEncoder
from lib.helper import strip_control_characters
from yarp import *

ServiceStartMode = {0: "Boot", 1: "System", 2: "Automatic", 3: "Manual", 4: "Disabled"}
Type = {1: "KernelDriver", 2: "FileSystemDriver", 4: "Adapter", 8: "RecognizerDriver", 16: "Win32OwnProcess", 32: "Win32ShareProcess", 256: "InteractiveProcess"}
service = {'Timestamp': 'N/A', 'Launch String': 'ControlSet001\Services', 'Name': 'N/A', 'DisplayName': 'N/A', 'Description': 'N/A', 'ImagePath': 'N/A',
            'Start As': 'N/A', 'Mode': 'N/A', 'Category': 'Service', 'Service Dll': 'N/A'}
class Services():
    
    def __init__(self,prim_hive):
        self.prim_hive = prim_hive
       
    def GetService(self, Service):
        for x in Service.values():
            if x.name() == 'Description':
                service['Description'] = strip_control_characters(x.data())
            elif x.name() == 'DisplayName':
                service['DisplayName'] = strip_control_characters(x.data())
            elif x.name() == 'ImagePath':
                service['ImagePath'] = strip_control_characters(x.data())
            elif x.name() == 'ObjectName':
                service['Start As'] = strip_control_characters(x.data())
            elif x.name() == 'Start':
                service['Mode'] = ServiceStartMode[x.data()]
            elif x.name() == 'Type':
                try:
                    service['Type'] = Type[x.data()]
                except KeyError:
                    continue 

    def run(self):
        lst_json = []
        lst_csv = []
        "use the SYSTEM && SOFTWARE hive to get the result"
        hive = Registry.RegistryHive(open(self.prim_hive, 'rb'))
        REG_Path_1 = u'ControlSet001\Services'
        Key = hive.find_key(REG_Path_1)
        if Key:
            for Subkey in Key.subkeys():
                service['Name'] = Subkey.name()
                service['@timestamp'] = Subkey.last_written_timestamp().isoformat()
                self.GetService(Subkey)
                Para_Path = u'ControlSet001\Services\\' + Subkey.name() + '\\Parameters'
                Para_Key = hive.find_key(Para_Path)
                if Para_Key:
                    for y in Para_Key.values():
                        if y.name() == 'ServiceDll':
                            service['Service Dll'] = strip_control_characters(y.data())
                else:
                    continue
                lst_json.append(u"{}".format(json.dumps(service.copy(), cls=ComplexEncoder)))
                lst_csv.append(service.copy())
        else:
            logging.info(u"[{}] {} not found.".format('Services', REG_Path_1))
        
        return lst_json, lst_csv, service.keys()
