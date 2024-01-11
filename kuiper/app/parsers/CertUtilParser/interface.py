import os
import sys
import subprocess
import json

def auto_interface(file,parser):
    try:
        fullpath = os.path.abspath(file)
        CurrentPath=os.path.dirname(os.path.abspath(__file__))
        proc = subprocess.Popen('python3 "'+ CurrentPath+'/CryptnetUrlCacheParser.py" -f "' + file + '" --useContent --outputFormat jsonl', shell=True ,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        res = json.loads(proc.stdout.read())
        res["@timestamp"] = res.pop("Timestamp")
        return [res]
    except Exception as e:
        exc_type,exc_obj,exc_tb = sys.exc_info()
        msg = "[-] [Error] " + str(parser) + " Parser: " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        print(msg)
        return (None , msg)
