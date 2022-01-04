
import sys
import os 
import subprocess
import ast
import json 


# return json in a beautifier
def json_beautifier(js):
    return json.dumps(js, indent=4, sort_keys=True)

def imain(file, parser):
    
    try:
        CurrentPath=os.path.dirname(os.path.abspath(__file__))


        cmd = 'python3 '+ CurrentPath+'/vol_Parser.py -k -f "' + file + '" -p ' + parser
        proc = subprocess.Popen(cmd, shell=True ,stdin=None , stdout=subprocess.PIPE , stderr=subprocess.PIPE)
        res , err = proc.communicate()
        if err != "":
            raise Exception(err.split("\n")[-2])
        
        res = res.split('\n')
        data = ""
        for line in res:
            if line.startswith('['):
                data += line
        if data == "":
            return []
        d = []
        for i in ast.literal_eval(data):
            if type(i) == dict:
                if len(i.keys()):
                    d.append(i)
                else:
                    continue
            else:
                d.append(json.loads(i) )
        return d


    except Exception as e:
        exc_type,exc_obj,exc_tb = sys.exc_info()
        msg = "[-] [Error] " + str(parser) + " Parser: " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        return (None , msg)

