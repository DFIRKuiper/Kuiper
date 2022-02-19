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


class Explorer():
    def __init__(self,prim_hive,log_files):
        self.prim_hive = prim_hive
        self.log_files = log_files
        
    def run(self):
        lst = []
        CLSID = []
        Launch_String = []
        "use the SOFTWARE && Ntuser hive to get the result"
        hive = get_hive(self.prim_hive,self.log_files)
        REG_Path_G1 = [ 'Wow6432Node\Microsoft\Windows\CurrentVersion\Explorer\ShellServiceObjects',
                        'Wow6432Node\Microsoft\Windows\CurrentVersion\Explorer\ShellIconOverlayIdentifiers',
                        'Microsoft\Windows\CurrentVersion\Explorer\ShellServiceObjects',
                        'Microsoft\Windows\CurrentVersion\Explorer\ShellIconOverlayIdentifiers',
                        'WOW6432Node\Classes\*\ShellEx\ContextMenuHandlers',
                        'WOW6432Node\Classes\*\ShellEx\PropertySheetHandlers',
                        'WOW6432Node\Classes\Drive\ShellEx\ContextMenuHandlers',
                        'WOW6432Node\Classes\AllFileSystemObjects\ShellEx\ContextMenuHandlers',
                        'WOW6432Node\Classes\AllFileSystemObjects\ShellEx\DragDropHandlers',
                        'WOW6432Node\Classes\AllFileSystemObjects\ShellEx\PropertySheetHandlers',
                        'WOW6432Node\Classes\Directory\ShellEx\ContextMenuHandlers',
                        'WOW6432Node\Classes\Directory\ShellEx\DragDropHandlers',
                        'WOW6432Node\Classes\Directory\ShellEx\PropertySheetHandlers',
                        'WOW6432Node\Classes\Directory\ShellEx\CopyHookHandlers',
                        'WOW6432Node\Classes\Folder\ShellEx\ContextMenuHandlers',
                        'WOW6432Node\Classes\Folder\ShellEx\DragDropHandlers',
                        'WOW6432Node\Classes\Folder\ShellEx\PropertySheetHandlers',
                        'WOW6432Node\Classes\Folder\ShellEx\ExtShellFolderViews',
                        'WOW6432Node\Classes\Folder\ShellEx\ColumnHandlers',
                        'WOW6432Node\Classes\Directory\Background\ShellEx\ContextMenuHandlers',
                        'Classes\*\ShellEx\ContextMenuHandlers',
                        'Classes\*\ShellEx\PropertySheetHandlers',
                        'Classes\Drive\ShellEx\ContextMenuHandlers',
                        'Classes\AllFileSystemObjects\ShellEx\ContextMenuHandlers',
                        'Classes\AllFileSystemObjects\ShellEx\DragDropHandlers',
                        'Classes\AllFileSystemObjects\ShellEx\PropertySheetHandlers',
                        'Classes\Directory\ShellEx\ContextMenuHandlers',
                        'Classes\Directory\ShellEx\DragDropHandlers',
                        'Classes\Directory\ShellEx\PropertySheetHandlers',
                        'Classes\Directory\ShellEx\CopyHookHandlers',
                        'Classes\Folder\ShellEx\ContextMenuHandlers',
                        'Classes\Folder\ShellEx\DragDropHandlers',
                        'Classes\Folder\ShellEx\PropertySheetHandlers',
                        'Classes\Folder\ShellEx\ExtShellFolderViews',
                        'Classes\Folder\ShellEx\ColumnHandlers',
                        'Classes\Directory\Background\ShellEx\ContextMenuHandlers',
                        u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\ShellServiceObjects',
                        u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\ShellIconOverlayIdentifiers',
                        u"\\Software\\Classes\\*\\shellex\\ContextMenuHandlers",
                        u'\\Software\\Classes\\*\\ShellEx\\PropertySheetHandlers',
                        u'\\Software\\Classes\*\shellex\ContextMenuHandlers',
                        u'\\Software\\Classes\\AllFileSystemObjects\\ShellEx\\ContextMenuHandlers',
                        u'\\Software\\Classes\\AllFileSystemObjects\\ShellEx\\DragDropHandlers',
                        u'\\Software\\Classes\\AllFileSystemObjects\\ShellEx\\PropertySheetHandlers',
                        u'\\Software\\Classes\\Directory\\ShellEx\\ContextMenuHandlers',
                        u'\\Software\\Classes\\Directory\\ShellEx\\DragDropHandlers',
                        u'\\Software\\Classes\\Directory\\ShellEx\\PropertySheetHandlers',
                        u'\\Software\\Classes\\Directory\\ShellEx\\CopyHookHandlers',
                        u'\\Software\\Classes\\Folder\\ShellEx\\ContextMenuHandlers',
                        u'\\Software\\Classes\\Folder\\ShellEx\\DragDropHandlers',
                        u'\\Software\\Classes\\Folder\\ShellEx\\PropertySheetHandlers',
                        u'\\Software\\Classes\\Folder\\ShellEx\\ExtShellFolderViews',
                        u'\\Software\\Classes\\Folder\\ShellEx\\ColumnHandlers',
                        u'\\Software\\Classes\\Directory\\Background\\ShellEx\\ContextMenuHandlers',
                        ]
        
        REG_Path_G2 = [ 'Classes\Protocols\Handler\ms-help',
                        'Classes\Protocols\Handler\mso-minsb.16',
                        'Classes\Protocols\Handler\osf.16',
                        u'\\Software\\Classes\\Protocols\\Handler\\ms-help',
                        u'\\Software\\Classes\\Protocols\\Handler\\mso-minsb.16',
                        u'\\Software\\Classes\\Protocols\\Handler\\osf.16']
        
        REG_Path_G3 = [ 'Classes\Protocols\Filter\\text/xml',
                        u'\\Software\\Classes\\Protocols\\Filter\\text/xml',
                        'WOW6432Node\Microsoft\Windows\CurrentVersion\ShellServiceObjectDelayLoad',
                        'Microsoft\Windows\CurrentVersion\ShellServiceObjectDelayLoad',
                        u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\ShellServiceObjectDelayLoad',
                        'Microsoft\Windows\CurrentVersion\Explorer\ShellExecuteHooks',
                        'Wow6432Node\Microsoft\Windows\CurrentVersion\Explorer\ShellExecuteHooks',]
        
        REG_Path_G4 = ['Wow6432Node\Microsoft\Windows\CurrentVersion\Explorer\SharedTaskScheduler',
                       'Microsoft\Windows\CurrentVersion\Explorer\SharedTaskScheduler',
                       'Wow6432Node\Microsoft\Ctf\LangBarAddin',
                       'Microsoft\Ctf\LangBarAddin',
                       u'\\Software\\Wow6432Node\\Microsoft\\Ctf\\LangBarAddin',
                       u'\\Software\\Microsoft\\Ctf\\LangBarAddin']

        REG_Path_G5 = u'SOFTWARE\\Microsoft\\Internet Explorer\\Desktop\\Components'
        
        ##########
        ##Group 1
        ##########
        for p in REG_Path_G1:
            Key = hive.find_key(p)
            if Key:
                for SK in Key.subkeys():
                    if SK.name().startswith('{'):
                        CLSID.append(SK.name())
                        Launch_String.append(p)
                    else:
                        for x in SK.values():
                            CLSID.append(x.data()[:-1])
                            Launch_String.append(p)
            else:
                logging.info(u"[{}] {} not found.".format('Explorer', p))
        ##########
        ##Group 2
        ##########
        for p in REG_Path_G2:
            Key = hive.find_key(p)
            if Key:
                for x in Key.values():
                    if x.name() == "CLSID":
                        CLSID.append(x.data()[:-1])
                        Launch_String.append(p)
            else:
                logging.info(u"[{}] {} not found.".format('Explorer', p))
        ##########
        ##Group 3
        ##########
        for p in REG_Path_G3:
            Key = hive.find_key(p)
            if Key:
                for x in Key.values():
                    CLSID.append(x.data()[:-1])
                    Launch_String.append(p)
                    
            else:
                logging.info(u"[{}] {} not found.".format('Explorer', p))
        ##########
        ##Group 4
        ##########
        for p in REG_Path_G4:
            Key = hive.find_key(p)
            if Key:
                for x in Key.values():
                    Path = strip_control_characters(x.data())
                    TS = Bin_key.last_written_timestamp().isoformat()
                    record = OrderedDict([
                        ("@timestamp",TS),
                        ("Launch String", REG_Path_G5),
                        ("Category", "Explorer"),
                        ("Path", Path)
                    ])
                    lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
                    
            else:
                logging.info(u"[{}] {} not found.".format('Explorer', p))
        ##########
        ##Group 5
        ##########
        Key = hive.find_key(REG_Path_G5)
        if Key:
            for SK in Key.subkeys():
                for x in SK.values():
                    if x.name() == "Source":
                        Path = strip_control_characters(x.data())
                        TS = Bin_key.last_written_timestamp().isoformat()
                        record = OrderedDict([
                            ("@timestamp",TS),
                            ("Launch String", REG_Path_G5),
                            ("Category", "Explorer"),
                            ("Path", Path)
                        ])
                    lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
            else:
                logging.info(u"[{}] {} not found.".format('Explorer', p))
        ##########
        ##Get BIN 
        ##########
        for ID, LS in zip(CLSID, Launch_String):
            CLSID_path = ["Wow6432Node\Classes\CLSID\\" + ID + "\InprocServer32",
                          "Classes\CLSID\\" + ID + "\InprocServer32",
                          "Wow6432Node\Classes\CLSID\\" + ID + "\InprocServer32",
                          "Classes\CLSID\\" + ID + "\InprocServer32"]
            for p in CLSID_path:
                Bin_key = hive.find_key(p)
                if Bin_key:
                    for y in Bin_key.values():
                        if y.name() == "":
                            Path = strip_control_characters(y.data())
                            TS = Bin_key.last_written_timestamp().isoformat()
                            record = OrderedDict([
                                ("@timestamp",TS),
                                ("Launch String", LS),
                                ("Category", "Explorer"),
                                ("Path", Path)
                            ])
                            lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
            
                else:
                    logging.info(u"[{}] {} not found.".format('Explorer', Bin_key))

        return lst
