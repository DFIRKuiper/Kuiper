import json
import logging
import traceback
from collections import OrderedDict
from lib.helper import convert_datetime
from lib.helper import ComplexEncoder
from lib.hive_yarp import get_hive
from yarp import *


class Amcache():

    def __init__(self,prim_hive,log_files):
        self.prim_hive = prim_hive
        self.log_files = log_files

    def run(self):
        lst =[]
        hive = get_hive(self.prim_hive,self.log_files)
        Amcache_user_settings_path = u"root\\InventoryApplicationFile"
        Amcache_user_settings_key = hive.find_key(Amcache_user_settings_path)
        if Amcache_user_settings_key :
            for sid_key in Amcache_user_settings_key.subkeys():
                sub_key  = sid_key.name()
                value_X = sid_key.values()
                path = sid_key.value(name=u"LowerCaseLongPath").data()
                hash = sid_key.value(name=u"FileId").data()
                Name = sid_key.value(name=u"Name").data()
                Publisher =sid_key.value(name=u"Publisher").data()
                Version =sid_key.value(name=u"Version").data()
                BinFileVersion=sid_key.value(name=u"BinFileVersion").data()
                BinaryType=sid_key.value(name=u"BinaryType").data()
                ProductName=sid_key.value(name=u"ProductName").data()
                ProductVersion=sid_key.value(name=u"ProductVersion").data()
                LinkDate=sid_key.value(name=u"LinkDate").data()
                BinProductVersion=sid_key.value(name=u"BinProductVersion").data()
                Size=sid_key.value(name=u"Size").data()
                Language=sid_key.value(name=u"Language").data()
                IsPeFile=sid_key.value(name=u"IsPeFile").data()
                record = OrderedDict([
                    ("path", path),
                    ("hash", hash),
                    ("Name", Name),
                    ("Publisher", Publisher),
                    ("Version", Version),
                    ("BinFileVersion", BinFileVersion),
                    ("BinaryType", BinaryType),
                    ("ProductName", ProductName),
                    ("ProductVersion", ProductVersion),
                    ("LinkDate", LinkDate),
                    ("BinProductVersion", BinProductVersion),
                    ("ProductName", ProductName),
                    ("Size", Size),
                    ("Language", Language),
                    ("IsPeFile", IsPeFile),
                    ("@timestamp", LinkDate),
                ])

                lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
            return lst
        else:
            logging.info(u"[{}] {} not found.".format('Amcache', Amcache_user_settings_key))
