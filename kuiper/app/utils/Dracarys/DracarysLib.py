import sys
sys.path.append("..")
from Rhaegal.RhaegalLib import Event,Rhaegal
import csv
import argparse
import os
import fnmatch
import json
import logging
import time

__author__ = "AbdulRhman Alfaifi"
__version__ = "1.0"
__maintainer__ = "AbdulRhman Alfaifi"
__license__ = "GPL"
__status__ = "Development"


def InitLogger(logName="Dracarys.log",log_level="INFO"):
    logger = logging.getLogger("Dracarys")

    if log_level == 'INFO':
        handler = logging.StreamHandler()
    else:
        handler = logging.FileHandler(logName,"w+")
    
    formatter = logging.Formatter('%(asctime)s [ %(levelname)-0s ] %(message)s',datefmt="%Y-%m-%dT%H:%M:%SZ")
    handler.setFormatter(formatter)
    handler.formatter.converter = time.gmtime
    logger.addHandler(handler)
    logger.setLevel(log_level)
    return logger

class Dracarys:
    def __init__(self,rhaegal=None,mapper=None):
        self.rhaegal = rhaegal
        self.mapper = mapper

        
    def Scan(self, filePath=None , json_records=None):
        if filePath is not None:
            if os.path.isfile(filePath):
                # if provided file is csv
                if filePath.lower().endswith("csv"):
                    for record in self.CSVToJSON(filePath):
                        for rule, event, matchedStr in self.MatchAll(record):
                            yield rule, event, matchedStr

                # if provided file is an iis log file
                elif fnmatch.fnmatch(filePath.lower(),"*u_ex??????.log"):
                    for record in self.IISToJSON(filePath):
                        for rule, event, matchedStr in self.MatchAll(record):
                            
                            yield rule, event, matchedStr
                

                # if provided file is kjson format (kuiper json format)
                elif filePath.endswith("kjson"):
                    with open(filePath) as inFile:
                        for record in inFile:
                            krecord = json.loads(record)
                            record  = krecord['Data']
                            record["Channel"] = krecord['data_type']
                            for rule,event,matchedStr in self.MatchAll(record):
                                del event.EventData['Channel']
                                krecord['Data'] = event.EventData
                                event.EventData = krecord
                                yield rule, event, matchedStr

                # if provided file is a regular json file
                elif filePath.lower().endswith("json"):
                    with open(filePath) as inFile:
                        for record in inFile:
                            record = json.loads(record)
                            record["Channel"] = filePath
                            for rule,event,matchedStr in self.MatchAll(record):
                                yield rule, event, matchedStr

                else:
                    if self.rhaegal.logger:
                        self.rhaegal.logger.warning(f"can not process the file '{filePath}'")
            else:
                raise ValueError(f"The function 'Dracarys.Scan' only acceptes file path")




        elif json_records is not None:
            for record in json_records:
                record["Channel"] = record['data_type'] if 'data_type' in record else None
                for rule,event,matchedStr in self.MatchAll(record):
                    yield rule, event, matchedStr

        else:
            raise ValueError(f"The function 'Dracarys.Scan' should receive either file path or json record")
    
    # this function will try to find if the record match any of the rules
    def MatchAll(self,record):
        eventObj = Event(raw=record)
        for rule in self.rhaegal.ruleSet:
            matchedStr = self.rhaegal.match(rule,eventObj)
            if matchedStr:
                eventObj.EventData['rhaegal'] = rule.getRuleDetails()
        
        yield rule,eventObj,matchedStr

    # this function convert csv to json,
    def CSVToJSON(self,filePath):
        with open(filePath) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            headers = next(csv_reader,None)
            for row in csv_reader:
                res = {"Channel":filePath}
                for i,col in enumerate(headers):
                    try:
                        res[col]=row[i]
                    except IndexError:
                        res[col]=''
                    except Exception as e:
                        if self.rhaegal.logger:
                            self.rhaegal.logger.error(e)
                yield res

    # this function will convert the IIS logs to json format
    def IISToJSON(self,filePath):
        with open(filePath) as log:
            for record in log:
                if record.startswith("#"):
                    if record.startswith("#Fields: "):
                        fields = record.replace("#Fields: ","").split()
                    else:
                        continue
                else:
                    recordParts = record.split()
                    res = {"Channel":filePath}
                    for i,field in enumerate(fields):
                        try:
                            res[field]=recordParts[i]
                        except Exception as e:
                            if self.rhaegal.logger:
                                self.rhaegal.logger.error(e)
                    yield res
                
