import os
import subprocess
import json 
import ast
import sys



def Netlogon_interface(file , parser):

    try:
        CurrentPath=os.path.dirname(os.path.abspath(__file__))
        cmd = 'python3 '+ CurrentPath+'/Netlogon_Logs_Parser.py '+ file
        proc = subprocess.Popen(cmd, shell=True ,stdin=None , stdout=subprocess.PIPE , stderr=subprocess.PIPE)
        dd , err = proc.communicate()
        err = err.decode("utf-8")

        if err != "":
            raise Exception(err.split("\n")[-2])
        decoded_data = dd.decode("utf-8")

        if decoded_data != '':
            #print(ast.literal_eval(decoded_data))            
            return [json.loads(i) for i in  ast.literal_eval(decoded_data)]
        return []
                
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        msg = "Failed " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        return (None , msg)

