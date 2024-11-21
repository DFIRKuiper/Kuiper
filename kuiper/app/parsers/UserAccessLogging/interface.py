import os
import sys
import subprocess
import json
import ast

def auto_interface(file,parser):

    try:
        CurrentPath=os.path.dirname(os.path.abspath(__file__))

        cmd = 'python3 '+ CurrentPath+'/KStrike.py  "' + file.replace("$" , '\$') +'"'
        proc = subprocess.Popen(cmd, shell=True ,stdin=None , stdout=subprocess.PIPE , stderr=subprocess.PIPE)
        res , err = proc.communicate()
        if err != "":
            raise Exception(err.split("\n"))

        res = str(res).split('\n')

        d = []
        for i in res:
            if i == "":
                continue
            else:
                d.append(json.loads(i) )
        return d


    except Exception as e:
        exc_type,exc_obj,exc_tb = sys.exc_info()
        msg = "[-] [Error] " + str(parser) + " Parser: " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        return (None , msg)

