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


class Logon():
    def __init__(self,prim_hive,log_files):
        self.prim_hive = prim_hive
        self.log_files = log_files

    def run(self):
        lst = []
        "use the SOFTWARE && SYSTEM && Ntuser hive to get the result"
        Registry_Path_G1 = u'Microsoft\Windows NT\CurrentVersion\Winlogon'
        
        SK_Name_G2 = ['DllName', 'script', 'script', 'script', 'script', 'script', 'script', 'script', 'script', 'StubPath', 'StubPath',
                      'script', 'script', 'script', 'script', ]
        Registry_Path_G2 = ['Microsoft\Windows NT\CurrentVersion\Winlogon\GPExtensions',
                            'Policies\Microsoft\Windows\System\Scripts\Startup',
                            'Policies\Microsoft\Windows\System\Scripts\Shutdown',
                            'Policies\Microsoft\Windows\System\Scripts\Logon',
                            'Policies\Microsoft\Windows\System\Scripts\Logoff',
                            'Microsoft\Windows\CurrentVersion\Group Policy\Scripts\Startup',
                            'Microsoft\Windows\CurrentVersion\Group Policy\Scripts\Shutdown',
                            'Microsoft\Windows\CurrentVersion\Group Policy\Scripts\Logon',
                            'Microsoft\Windows\CurrentVersion\Group Policy\Scripts\Logoff',
                            'Microsoft\Active Setup\Installed Components',
                            'Wow6432Node\Microsoft\Active Setup\Installed Components',
                            u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Group Policy\\Scripts\\Startup',
                            u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Group Policy\\Scripts\\Shutdown',
                            u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Group Policy\\Scripts\\Logon',
                            u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Group Policy\\Scripts\\Logoff'
                            ]
        SK_Name_G3 = ['Shell', 'AlternateShell', 'AvailableShells', 'StartupPrograms','Common Startup','Common AltStartup', 'IconServiceLib',
                      'UserInitMprLogonScript', 'Shell', 'Load', 'Run', 'Startup','AltStartup', 'Startup','AltStartup']
        Registry_Path_G3 = [
                            u'ControlSet001\Control\SafeBoot',
                            'Microsoft\Windows NT\CurrentVersion\Winlogon\AlternateShells',
                            u'ControlSet001\Control\Terminal Server\WinStations\RDP-Tcp',
                            'Microsoft\Windows\CurrentVersion\Explorer\Shell Folders',
                            'Microsoft\Windows\CurrentVersion\Explorer\Shell Folders',
                            'Microsoft\Windows NT\CurrentVersion\Windows',
                            u'\\Environment',
                            u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System',
                            u'\\Software\\Microsoft\\Windows NT\\CurrentVersion\\Windows',
                            u'\\Software\\Microsoft\\Windows NT\\CurrentVersion\\Windows',
                            u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\User Shell Folders',
                            u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Folders'
                            ]
        Registry_Path_G4 = ['Microsoft\Windows NT\CurrentVersion\Terminal Server\Install\Software\Microsoft\Windows\CurrentVersion\Runonce',
                            'Microsoft\Windows NT\CurrentVersion\Terminal Server\Install\Software\Microsoft\Windows\CurrentVersion\RunonceEx',
                            'Microsoft\Windows NT\CurrentVersion\Terminal Server\Install\Software\Microsoft\Windows\CurrentVersion\Run',
                            'Microsoft\Windows NT\CurrentVersion\Terminal Server\Software\Microsoft\Windows\CurrentVersion\Run',
                            'Microsoft\Windows\CurrentVersion\Run',
                            'Microsoft\Windows\CurrentVersion\RunOnce',
                            'Microsoft\Windows\CurrentVersion\RunOnceEx',
                            'Wow6432Node\Microsoft\Windows\CurrentVersion\Run',
                            'Wow6432Node\Microsoft\Windows\CurrentVersion\RunOnce',
                            'Wow6432Node\Microsoft\Windows\CurrentVersion\RunOnceEx',
                            'Microsoft\Windows\CurrentVersion\Policies\Explorer\Run',
                            u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer\\Run',
                            u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Run',
                            u'\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce',
                            u'\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnceEx',
                            u'\\Software\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Run',
                            u'\\Software\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\RunOnce',
                            u'\\Software\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\RunOnceEx',
                            u'\\Software\\Microsoft\\Windows NT\\CurrentVersion\\Terminal Server\\Install\\Software\\Microsoft\\Windows\\CurrentVersion\\Runonce',
                            u'\\Software\\Microsoft\\Windows NT\\CurrentVersion\\Terminal Server\\Install\\Software\\Microsoft\\Windows\\CurrentVersion\\RunonceEx',
                            u'\\Software\\Microsoft\\Windows NT\\CurrentVersion\\Terminal Server\\Install\\Software\\Microsoft\\Windows\\CurrentVersion\\Run'
                            ]
        Registry_Path_G5 = [
                            'Microsoft\Windows CE Services\AutoStartOnConnect',
                            'Microsoft\Windows CE Services\AutoStartDisconnect',
                            'Microsoft\Windows CE Services\AutoStartOnDisconnect',
                            'Wow6432Node\Microsoft\Windows CE Services\AutoStartOnConnect',
                            'Wow6432Node\Microsoft\Windows CE Services\AutoStartDisconnect',
                            'Wow6432Node\Microsoft\Windows CE Services\AutoStartOnDisconnect'
                            ]
        Registry_Path_G6 = ['Microsoft\Windows NT\CurrentVersion\Terminal Server\Install\Software\Microsoft\Windows\CurrentVersion\RunonceEx',
                            'Microsoft\Windows\CurrentVersion\RunOnceEx',
                            'Wow6432Node\Microsoft\Windows\CurrentVersion\RunOnceEx',
                            u'\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnceEx',
                            u'\\Software\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\RunOnceEx',
                            u'\\Software\\Microsoft\\Windows NT\\CurrentVersion\\Terminal Server\\Install\\Software\\Microsoft\\Windows\\CurrentVersion\\RunonceEx'
                            ]
                            
        hive = get_hive(self.prim_hive,self.log_files)
        ##########
        ##Group 1
        ##########
        Registry_Key_G1 = hive.find_key(Registry_Path_G1)
        if Registry_Key_G1:
            for x in Registry_Key_G1.values():
                if x.name() == 'VMApplet' or x.name() == 'Userinit' or x.name() == 'Shell' or x.name() == 'TaskMan' or x.name() == 'AppSetup' :
                    TS = Registry_Key_G1.last_written_timestamp().isoformat()
                    Path = strip_control_characters(x.data())
                    record = OrderedDict([
                        ("@timestamp",TS),
                        ("Launch String", Registry_Path_G1),
                        ("Name", x.name()),
                        ("Category", "Logon"),
                        ("Path", Path)
                    ])
                    lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder))) 
        else:
            logging.info(u"[{}] {} not found.".format('Logon', Registry_Path_G1))
        ##########
        ##Group 2
        ##########
        for key_path, SKN in zip(Registry_Path_G2, SK_Name_G2):
            key = hive.find_key(key_path)
            if key:
                for SK in key.subkeys():
                    for x in SK.values():
                        if x.name() == SKN:
                            TS = key.last_written_timestamp().isoformat()
                            Path = strip_control_characters(x.data())
                            record = OrderedDict([
                                ("@timestamp",TS),
                                ("Launch String", key_path),
                                ("Name", x.name()),
                                ("Category", "Logon"),
                                ("Path", Path)
                            ])
                        lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
            else:
                logging.info(u"[{}] {} not found.".format('Logon', key))
        ##########
        ##Group 3
        ##########
        for key_path, SKN in zip(Registry_Path_G3, SK_Name_G3):
            key = hive.find_key(key_path)
            if key:
                for x in key.values():
                    if x.name() == SKN:
                        TS = key.last_written_timestamp().isoformat()
                        Path = strip_control_characters(x.data())
                        record = OrderedDict([
                            ("@timestamp",TS),
                            ("Launch String", key_path),
                            ("Name", x.name()),
                            ("Category", "Logon"),
                            ("Path", Path)
                        ])
                        lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
            else:
                logging.info(u"[{}] {} not found.".format('Logon', key))
        ##########
        ##Group 4
        ##########
        for key_path in Registry_Path_G4:
            key = hive.find_key(key_path)
            if key:
                for x in key.values():
                    TS = key.last_written_timestamp().isoformat()
                    Path = strip_control_characters(x.data())
                    record = OrderedDict([
                        ("@timestamp",TS),
                        ("Launch String", key_path),
                        ("Name", x.name()),
                        ("Category", "Logon"),
                        ("Path", Path)
                    ])
                    lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
            else:
                logging.info(u"[{}] {} not found.".format('Logon', key))
        ##########
        ##Group 5
        ##########
        for key_path in Registry_Path_G5:
            key = hive.find_key(key_path)
            if key:
                for SK in key.subkeys():
                    for x in SK.values():
                        TS = key.last_written_timestamp().isoformat()
                        Path = strip_control_characters(x.data())
                        record = OrderedDict([
                            ("@timestamp",TS),
                            ("Launch String", key_path),
                            ("Name", x.name()),
                            ("Category", "Logon"),
                            ("Path", Path)
                        ])
                    lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
            else:
                logging.info(u"[{}] {} not found.".format('Logon', key))
        ##########
        ##Group 6
        ##########
        for key_path in Registry_Path_G5:
            key = hive.find_key(key_path)
            if key:
                for SK in key.subkeys():
                    path = key_path + '\\' + SK.name() + '\\\Depend'
                    key = hive.find_key(key_path)
                    if key:
                        for x in SK.values():
                            TS = key.last_written_timestamp().isoformat()
                            Path = strip_control_characters(x.data())
                            record = OrderedDict([
                                ("@timestamp",TS),
                                ("Launch String", key_path),
                                ("Name", x.name()),
                                ("Category", "Logon"),
                                ("Path", Path)
                            ])
                            lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
                    else:
                        logging.info(u"[{}] {} not found.".format('Logon', key))
            else:
                logging.info(u"[{}] {} not found.".format('Logon', key))

        
        return lst
