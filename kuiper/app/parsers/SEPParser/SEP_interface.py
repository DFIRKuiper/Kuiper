import os
import sys
import subprocess
import json

def auto_interface(file,parser):
    try:
        CurrentPath=os.path.dirname(os.path.abspath(__file__))
        cmd = 'python3 '+ CurrentPath+'/SEPparser.py -f \'' + file.replace("$" , '/$') + '\''
        proc = subprocess.Popen(cmd, shell=True ,stdin=None , stdout=subprocess.PIPE , stderr=subprocess.PIPE)
        res , err = proc.communicate()
        if err != b'' and err != "":
            raise Exception(err)
            

        res = res.split(b"\n")
        for line in res:
            if line.startswith(b"["):
                res = line

        if res == "":
            return []
        # else:
        #     res = SEPparser.remove_null(res)
        data = json.loads(res)
            
        return data
        
    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        msg = parser + " Parser: " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        return (None , msg)
