import logging
import json
from lib.helper import ComplexEncoder
from lib.helper import strip_control_characters
from yarp import *

Entry = {'@timestamp': 'N/A', 'Launch String': 'N/A', 'Category': 'CompresseApp', 'App':'N/A', 'Operation': 'N/A', 'Path': 'N/A'}
lst_json = []
lst_csv = []
class CompresseApp():
    def __init__(self,prim_hive):
        self.prim_hive = prim_hive
    
    def GetKeyValue(self, key, app, Operation,data):
        Entry['@timestamp'] = key.last_written_timestamp().isoformat()
        Entry['Launch String'] = key.path()
        Entry['App'] = app
        Entry['Operation'] = Operation
        Entry['Path'] = data
        lst_json.append(u'{}'.format(json.dumps(Entry.copy(), cls=ComplexEncoder)))
        lst_csv.append(Entry.copy())

    def run(self):
        
        'use the Ntuser hive to get the result'
        REGPath = ['Software\\7-Zip\\Compression',
                    'Software\\7-Zip\\Extraction',
                    'Software\\WinRAR\\ArcHistory']
        hive = Registry.RegistryHive(open(self.prim_hive, 'rb'))
        for Path in REGPath:
            Registry_Key = hive.find_key(Path)
            if Registry_Key:
                for x in Registry_Key.values():
                    if x.name() == 'ArcHistory' or x.name() == 'PathHistory':
                        Op = Path.split('Zip\\', 1)
                        self.GetKeyValue(Registry_Key, '7-Zip', Op[1], x.data().decode('ascii').replace(u'\x00',''))                        
                    elif Registry_Key.name() == 'ArcHistory':
                        self.GetKeyValue(Registry_Key, 'WinRAR', 'Compression', x.data().replace(u'\x00',''))
            else:
                logging.info(u'[{}] {} not found.'.format('CompresseApp', Path))        

        return lst_json, lst_csv, Entry.keys()
        