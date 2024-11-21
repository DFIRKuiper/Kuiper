import os
import sys
import subprocess
import json

def interface(file,parser):
    try:
        fullpath = os.path.abspath(file).replace("$","\\$")
        CurrentPath = os.path.dirname(os.path.abspath(__file__))
        proc = subprocess.Popen('python3 "'+ CurrentPath+'/sds_parser_cli.py" "' + fullpath + '"', shell=True ,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        results = []

        for record in proc.stdout.readlines():
            record = json.loads(record.strip())
            sd = record.pop("security_descriptor")
            record["owner_sid"] = sd.get("owner_sid", None)
            record["group_sid"] = sd.get("group_sid", None)
            results.append(record)
            
        return results
        
    except Exception as e:
        _,exc_obj,exc_tb = sys.exc_info()
        msg = "[-] [Error] " + str(parser) + " Parser: " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        print(msg)
        return (None , msg)