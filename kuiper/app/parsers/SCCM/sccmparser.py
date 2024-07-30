import os
import sys
import re
from dateutil import parser
import datetime
import json 
def find_between_r( s, first, last ):
    try:
        start = s.rindex( first ) + len( first )
        end = s.rindex( last, start )
        return s[start:end]
    except ValueError:
        return ""

def parse_sccm(file_path):
    try:
        file = open(file_path,"r")
        lines = file.readlines()
        lst =[]
        for line in lines:
            val_lst = line.split("><")
            dict = {}
            dict['event'] = find_between_r(line,'<![LOG[',']LOG]!>')

            if "assetadvisor" in file_path.lower():
                if "Add RecentlyUsedApp" in dict["event"]:
                    fileNameAndUsername = dict["event"].split(": <")[1]
                    username = fileNameAndUsername.strip(">").split(".exe ")[-1]
                    fileName = fileNameAndUsername.strip(">").split(".exe")[0]+".exe"
                    dict["username"] = username
                    dict["filename"] = fileName
                elif "GetFileVersionInfoSize failed for file" in dict["event"]:
                    path = dict["event"].split("GetFileVersionInfoSize failed for file ")[1].split(",")[0]
                    filename = path.split("\\")[-1]
                    dict["path"] = path
                    dict["filename"] = filename
                elif "Successfully executed " in dict["event"]:
                    query = dict["event"].split("Successfully executed ")[1].replace(" query","")
                    dict["query"] = query
            elif "mtrmgr" in file_path.lower():
                if "Process ID" in dict["event"]:
                    processid = dict["event"].split(" ID ")[1].split(" is ")[0]
                    path = dict["event"].split(" process ")[1]
                    dict["processid"] = processid
                    dict["path"] = path
                if "GetFileVersionInfoSize" in dict["event"]:
                    dict["path"] = dict["event"].split("GetFileVersionInfoSize failed for file ")[1].split(", ")[0]
            val2 = val_lst[1].replace(">","").rstrip().split(" ")
            for val in val2:
                fval = val.split("=")
                dict[fval[0].strip('\"')]=fval[1].strip('\"')
            date_time_str= dict['date']+" "+dict["time"].replace("-180","")
            date_time = dt = parser.parse(date_time_str)
            dict['@timestamp'] = date_time.isoformat()

            lst.append(dict)
        return json.dumps(lst)
    except:
        pass


print(parse_sccm(sys.argv[1]))
