import sys
import os
import xml.etree.ElementTree as ET
import json
from collections import OrderedDict


class Ichnaea:
    def __init__(self, file):

        self.IIS_modules = self.get_IIS_modules_details(file)

    def get_IIS_modules_details(self, files):
        tree = ET.parse(files)
        root = tree.getroot()
        glopalModules = []
        for module in root.findall('./system.webServer/globalModules/'):
            glopalModules.append(module.attrib)
        return glopalModules