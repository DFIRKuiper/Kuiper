import sys
import os
import xml.etree.ElementTree as ET
import json
from collections import OrderedDict


class Ichnaea:
    def __init__(self, file):

        self.IIS_Sites = self.get_IIS_Sites_details(file)

    def get_IIS_Sites_details(self, files):
        tree = ET.parse(files)
        root = tree.getroot()
        virDirs = []
        for site in root.findall('./system.applicationHost/sites/'):
            for app in site.findall('./'):
                try:
                    for virDir in app.findall('./'):
                        if virDir.tag == "virtualDirectory":
                            siteDict = site.attrib
                            appDict = app.attrib
                            virDirDict = virDir.attrib
                            siteDict = {'Site ' + k: v for k, v in siteDict.items()} 
                            virDirDict["Virtual Path"] = appDict["path"] + virDirDict["path"]
                            virDirDict["Physical Path"] = virDirDict.pop("physicalPath")
                            siteDict.update(appDict)
                            siteDict.update(virDirDict)
                            virDirs.append(OrderedDict(siteDict))
                except Exception as e:
                    print(e)
        return virDirs