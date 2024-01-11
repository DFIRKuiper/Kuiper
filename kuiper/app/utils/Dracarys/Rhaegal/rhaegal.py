#!/usr/bin/env python3

import argparse
from RhaegalLib import Rhaegal
import RhaegalLib
from datetime import datetime
import os
import psutil
import sys
import logging
import zipfile
import time
import platform
startTime = time.time()

__author__ = "AbdulRhman Alfaifi"
__version__ = "1.1"
__maintainer__ = "AbdulRhman Alfaifi"
__license__ = "GPL"
__status__ = "Production"

parser = argparse.ArgumentParser(description='Rhaegal, Windows Event Logs Processing and Detection Tool')
parser.add_argument("-l","--log",help='The log you want to run the rules against')
parser.add_argument("-lp","--logsPath", help='A path that contains Windows Event Logs files (EVTX) to run the rules against')
parser.add_argument("-r","--rule", help='Rhaegal rule you want to use')
parser.add_argument("-rp","--rulesPath", help='Path that contains Rhaegal rules')
parser.add_argument("--headers", help='Print the headers',action="store_true",default=False)
parser.add_argument("-o","--output", help='Results output file (Defaults to stdout)')
parser.add_argument("-n","--threads", help='Number of threads to use (Default=10)',type=int,default=10)
parser.add_argument("--no-log", help='Do not create log file',action="store_true",default=False)
parser.add_argument("--log-file", help='Log file path',default="Rhaegal.log")
parser.add_argument("--log-level",choices=['CRITICAL','ERROR','WARNING','INFO','DEBUG'], help='Logging level (Defaults to INFO)',default="INFO")
parser.add_argument("-v","--version", help='Print version number',action="store_true",default=False)

def InitLogger(logName="Rhaegal.log",log_level="info"):
    logger = logging.getLogger("Rhaegal")

    if log_level == 'info':
        handler = logging.StreamHandler()
    else:
        handler = logging.FileHandler(logName,"w+")
    
    formatter = logging.Formatter('%(asctime)s [ %(levelname)-0s ] %(message)s',datefmt="%Y-%m-%dT%H:%M:%SZ")
    handler.setFormatter(formatter)
    handler.formatter.converter = time.gmtime
    logger.addHandler(handler)
    logger.setLevel(log_level)
    return logger

def Unzip():
    path = os.getcwd()
    zip_ref = zipfile.ZipFile("rules.zip", 'r')
    zip_ref.extractall(path)
    zip_ref.close()	


if "__main__" == __name__:
    args = parser.parse_args()
    if args.rulesPath:
        if not os.path.exists(args.rulesPath):
            Unzip()
    elif args.rule:
        if not os.path.isfile(args.rule):
            Unzip()
    if not args.no_log:
        logger = InitLogger(logName=args.log_file,log_level=args.log_level)
    else:
        logger=None
    p = psutil.Process(os.getpid())
    if "win" in sys.platform:
        p.nice(psutil.IDLE_PRIORITY_CLASS)
    else:
        p.nice(20)

    if args.version:
        print(f"Rhaegal v{__version__}")
        print(f"RhaegalLib v{RhaegalLib.__version__}")
        sys.exit()
    if not args.log and not args.logsPath:
        parser.error("Specify the logs to process. Use -l <logpath> or -lp <logsdir>")

    if not args.rule and not args.rulesPath:
        parser.error("Specify the rule/s to use. Use -r <rulepath> or -rp <rulesdir>")
    if logger:
        logger.info(f"Process started with the PID {os.getpid()}")
    if args.logsPath:
        # No Logging for multiprocessing
        rhaegal = Rhaegal(rulePath=args.rule,rulesDir=args.rulesPath,logger=logger)
        if len(rhaegal.ruleSet) == 0:
            raise Exception(f"{__file__} was not able to load the rules !")
    elif args.log:
        rhaegal = Rhaegal(rulePath=args.rule,rulesDir=args.rulesPath,logger=logger)
        if len(rhaegal.ruleSet) == 0:
            raise Exception(f"{__file__} was not able to load the rules !")
    
    dirOrFile = args.log if args.log else args.logsPath
    file = open(args.output,"w") if args.output else None
    if args.headers:
        if file:
            file.write('"Event Date And Time","EventRecordID/s","Rule Name","Rule Score","Discription","Refrence","Matched","Rule Return"\n')
        else:
            print('"Event Date And Time","EventRecordID/s","Rule Name","Rule Score","Discription","Refrence","Matched","Rule Return"')
    for alert in rhaegal.process(dirOrFile,args.threads):
            alert.outputAlert(file=file)

    endTime = time.time()
    if logger:
        logger.info(f"Rheagal took {endTime - startTime} seconds")

# multiprocessing : 58.42704248428345
# mutithreading   : 63.33633470535278